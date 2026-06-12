class NFP:
    __slots__ = ("fixed_item_index", "mobile_item_index", "polygons")

    def __init__(self, fixed_item_index, mobile_item_index):
        self.fixed_item_index = fixed_item_index
        self.mobile_item_index = mobile_item_index
        self.polygons = []

    def add_polygon(self, nfp_polygon):
        self.polygons.append(nfp_polygon)

    def __iter__(self):
        return iter(self.polygons)

    def __len__(self):
        return len(self.polygons)

    def __bool__(self):
        return bool(self.polygons)
    