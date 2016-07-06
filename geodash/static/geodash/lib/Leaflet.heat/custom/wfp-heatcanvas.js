L.HeatCanvas = L.Canvas.extend({

  _initContainer: function () {
    L.Canvas.prototype._initContainer.call(this); // init this._ctx
    this._heat = simpleheat(this._container);
  },

  updateOptions: function (options)
  {
    this.options.radius = options.radius;
    this.options.max = options.max;
    this.options.maxZoom = options.maxZoom;
    this.options.minOpacity = options.minOpacity;
    this.options.blur = options.blur;
    this.options.gradient = options.gradient;
  },

  beforeAdd: function(layer)
  {
    this._layers = {};
    this._layers[L.stamp(layer)] = layer;
  },

  onAdd: function()
  {
    L.Renderer.prototype.onAdd.call(this);
  },

  removeLayer: function(layer)
  {
    var layerID = L.stamp(layer);
    delete layer._removed;
    delete this._layers[layerID];
  },

  _redraw: function ()
  {
    this._ctx.clearRect(0, 0, this._container.width, this._container.height);

    // Double Check Layers
    for (var id in this._layers)
    {
      layer = this._layers[id];
      if(layer._removed)
      {
        delete layer._removed;
        delete this._layers[L.stamp(layer)];
      }
		}

    for (var id in this._layers) {
			layer = this._layers[id];
      layer._project(); // Reloads layer._pxBounds and projected coordinates
      this._draw(layer, layer._pxBounds);
		}
  },

  _draw: function (layer, bounds)
  {
    this._ctx.save();
    if(bounds)
    {
      // Doesn't work.  Need to clip by canvas points, not project points
      //this._ctx.rect(bounds.min.x, bounds.min.y, bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y);
      //this._ctx.clip(); // Clips canvas
    }
    var heatMapData = this.buildHeatMapData(this.options.radius, layer);
    this._heat.data(heatMapData);
    this._heat.draw(
      this.options.max,
      this.options.minOpacity,
      this.options.radius,
      this.options.blur,
      this._map.getZoom());
    this._ctx.restore();
  },

  buildHeatMapData: function (r, layer) {
    if (!this._map) {
        return;
    }

    var latlngs = layer._latlngs;

    if(latlngs.length == 0)
    {
        return [];
    }

    var data = [];
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
        //p = this._map.latLngToContainerPoint(latlngs[i]);
        p = this._map.latLngToLayerPoint(latlngs[i]);
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
