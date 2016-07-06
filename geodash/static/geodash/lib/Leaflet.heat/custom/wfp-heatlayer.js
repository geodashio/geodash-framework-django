L.HeatLayer = L.Path.extend({

  initialize: function (latlngs, options) {
    L.setOptions(this, options);

    this.options.minOpacity = this.options.minOpacity != undefined ? this.options.minOpacity : 0.05

    this._setLatLngs(latlngs);
	},

  beforeAdd: function (map) {
    this._renderer = map.getRenderer(this);
    this._renderer.updateOptions(this.options)
    L.HeatCanvas.prototype.beforeAdd.call(this._renderer, this);
	},

  onAdd: function() {
    L.HeatCanvas.prototype._redraw.call(this._renderer, this);
  },

  onRemove: function () {
		L.HeatCanvas.prototype.removeLayer.call(this._renderer, this);
    L.HeatCanvas.prototype._redraw.call(this._renderer, this);
	},

  _setLatLngs: function (latlngs) {
    this._bounds = new L.LatLngBounds();
    this._latlngs = this._convertLatLngs(latlngs);
    return this.redraw();
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
