
L.HeatCanvas = L.Canvas.extend({

  _initContainer: function () {
    L.Canvas.prototype._initContainer.call(this); // init this._ctx
    this._heat = simpleheat(this._container);
  },

  updateOptions: function (options)
  {
    this.options.max = options.max;
    this.options.maxZoom = options.maxZoom;

    this._heat.radius(options.radius || this._heat.defaultRadius, options.blur);

    if (options.gradient) {
        this._heat.gradient(options.gradient);
    }
    if (options.max) {
        this._heat.max(options.max);
    }
  },

  beforeAdd: function(layer)
  {
    //L.Canvas.prototype._updateDashArray.call(this, layer);
    this._layers = {};
    this._layers[L.stamp(layer)] = layer;
    this._layer = layer;
  },

  onAdd: function()
  {
    L.Renderer.prototype.onAdd.call(this);
    //this._draw(this._layer, null);
  },

  /*_initPath: function (layer) {
    L.Canvas.prototype._initPath.call(this, layer);
    //L.Canvas.prototype._updateDashArray.call(this, layer);
    this._layers[L.stamp(layer)] = layer;
  },

  _updatePath: function (layer) {
    this._redrawBounds = layer._pxBounds;
    this._draw(true);
    layer._project();
    layer._update();
    this._draw();
    this._redrawBounds = null;
	},*/

  _redraw: function ()
  {
    this._layer._project(); // Reloads layer._pxBounds and projected coordinates
    //var bounds = this._redrawBounds = this._layer._pxBounds;
    this._draw(this._layer, this._layer._pxBounds);
    //this._redrawBounds = null;
  },

  _draw: function (layer, bounds)
  {
    if(bounds)
    {
      this._ctx.rect(bounds.min.x, bounds.min.y, bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y);
      this._ctx.clip(); // Clips canvas
    }
    if(layer._removed)
    {
      delete layer._removed;
      delete this._layers[L.stamp(layer)];
    }
    var heatMapData = this.buildHeatMapData(layer);
    this._heat.data(heatMapData);
    this._heat.draw(this.options.minOpacity === undefined ? 0.05 : this.options.minOpacity);
  },

  buildHeatMapData: function (layer) {
    if (!this._map) {
        return;
    }

    var latlngs = layer._latlngs;

    if(latlngs.length == 0)
    {
        return [];
    }

    var data = [];
    var r = this._heat._r;
    var size = this._map.getSize();
    var bounds = new L.Bounds(L.point([-r, -r]), size.add([r, r])); // The bounds of the container

    var max = this.options.max === undefined ? 1 : this.options.max;
    var maxZoom = this.options.maxZoom === undefined ? this._map.getMaxZoom() : this.options.maxZoom;
    var v = 1 / Math.pow(2, Math.max(0, Math.min(maxZoom - this._map.getZoom(), 12)));
    var cellSize = r / 2;

    var grid = [];
    var panePos = this._map._getMapPanePos();
    var offsetX = panePos.x % cellSize;
    var offsetY = panePos.y % cellSize;
    var i, len, p, cell, x, y, j, len2, k;

    // console.time('process');
    for (i = 0, len = latlngs.length; i < len; i++) {
        p = this._map.latLngToContainerPoint(latlngs[i]);
        if (bounds.contains(p))  // Check if point is within the container bounds
        {
            x = Math.floor((p.x - offsetX) / cellSize) + 2;
            y = Math.floor((p.y - offsetY) / cellSize) + 2;
            //k = latlngs[i][2] * v;
            k = latlngs[i][2];

            grid[y] = grid[y] || [];
            cell = grid[y][x];

            if (!cell)
            {
                grid[y][x] = [p.x, p.y, k];
            }
            else
            {
                //cell[0] = (cell[0] * cell[2] + p.x * k) / (cell[2] + k); // x
                //cell[1] = (cell[1] * cell[2] + p.y * k) / (cell[2] + k); // y
                cell[2] = cell[2] + k; // cumulated intensity value
            }
        }
    }

    for (i = 0, len = grid.length; i < len; i++) {
        if (grid[i]) {
            for (j = 0, len2 = grid[i].length; j < len2; j++) {
                cell = grid[i][j];
                if (cell) {
                    data.push([
                        Math.round(cell[0]),
                        Math.round(cell[1]),
                        Math.min(cell[2], max)
                    ]);
                }
            }
        }
    }
    return data;
  }
});

L.heatCanvas = function (options) {
	return L.Browser.canvas ? new L.HeatCanvas(options) : null;
};

L.HeatLayer = L.Path.extend({

  initialize: function (latlngs, options) {
    L.setOptions(this, options);
    this._setLatLngs(latlngs);
	},

  beforeAdd: function (map) {
    this._renderer = map.getRenderer(this);
    this._renderer.updateOptions(this.options)
    // Update Renderer HeatCanvas
    L.HeatCanvas.prototype.beforeAdd.call(this._renderer, this);
	},

  onAdd: function() {
    L.HeatCanvas.prototype._redraw.call(this._renderer, this);
  },

  _setLatLngs: function (latlngs) {
    this._bounds = new L.LatLngBounds();
    this._latlngs = this._convertLatLngs(latlngs);
    return this.redraw();

    // Previous
    //this._latlngs = latlngs;
    //return this.redraw();
  },

  _convertLatLngs: function (latlngs) {
    var result = [];
    for (var i = 0, len = latlngs.length; i < len; i++)
    {
      result[i] = latlngs[i];
      this._bounds.extend(L.latLng(latlngs[i][0], latlngs[i][1]));
    }
    return result;
  },

  addLatLng: function (latlng, latlngs) {

    //latlngs = latlngs || this._defaultShape();
    latlngs = latlngs || this._latlngs;
    //latlng = L.latLng(latlng[0]);
    latlngs.push(latlng);
    this._bounds.extend(L.latLng(latlng[0], latlng[1]));
    return this.redraw();
  },


  getBounds: function () {
  	return this._bounds;
  },

  getLatLngs: function () {
		return this._latlngs;
	},

  isEmpty: function () {
		return !this._latlngs.length;
	},

  getCenter: function ()
  {
    var points = this._latlngs;
    var x = 0;
    var y = 0;
    for(var i = 0; i < points.length; i++)
    {
        x += points[i][0];
        y += points[i][1];
    }
    var center = [x / points.length , y / points.length ];
    return this._map.layerPointToLatLng(center);
  },

  _project: function () {
    var pxBounds = new L.Bounds();
    this._rings = [];
    this._projectLatlngs(this._latlngs, this._rings, pxBounds);

    var w = this._clickTolerance();
    var p = new L.Point(w, w);

    if (this._bounds.isValid() && pxBounds.isValid())
    {
      pxBounds.min._subtract(p);
      pxBounds.max._add(p);
      this._pxBounds = pxBounds;
    }
	},

	_projectLatlngs: function (latlngs, result, projectedBounds)
  {
    var ring = [];
		for (var i = 0; i < latlngs.length; i++)
    {
			ring[i] = this._map.latLngToLayerPoint(latlngs[i]);
			projectedBounds.extend(ring[i]);
		}
		result.push(ring);
	},

  _update: function () {
    if (!this._map) { return; }
    this._renderer._redraw();
  }

});

L.heatLayer = function (latlngs, options) {
    return new L.HeatLayer(latlngs, options);
};

L.HeatLayer.prototype._containsPoint = function (p, closed)
{
  //https://github.com/Leaflet/Leaflet/blob/master/src/layer/vector/Canvas.js#L325
	return false;
};
