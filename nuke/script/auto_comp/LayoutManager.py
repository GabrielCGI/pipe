import nuke
from common.utils import *

# ######################################################################################################################

_MARGIN_BACKDROP = (30, 40, 30, 30)
_DEFAULT_FONT_SIZE_BACKDROP = 40
_DEFAULT_COLOR_BACKDROP = (150, 150, 150)
_DEFAULT_LAYOUT_BACKDROP = "v"

_NODE_WIDTH = 80
_NODE_HEIGHT = 66
_BASE_DISTANCE = 120


# ######################################################################################################################


class LayoutManager:
    # Positions
    POS_TOP = 1
    POS_TOP_RIGHT = 2
    POS_RIGHT = 3
    POS_BOTTOM_RIGHT = 4
    POS_BOTTOM = 5
    POS_BOTTOM_LEFT = 6
    POS_LEFT = 7
    POS_TOP_LEFT = 8
    # Align
    ALIGN_START = 1
    ALIGN_CENTER = 2
    ALIGN_END = 3

    @staticmethod
    def __get_init_backdrop_data(long_name, parent_long_name):
        return {
            "long_name": long_name,
            "parent_long_name": parent_long_name,
            "nodes": [],
            "backdrops": {},
            "relation": None,
            "options": {},
            "visited": False}

    def __init__(self):
        self.__backdrops_data = LayoutManager.__get_init_backdrop_data("", None)
        self.__nodes_layout_data = {}
        self.__backdrops_layout_data = {}
        self.__current_workspace_y = None
        self.__bbox_graph = 0, 0, 0, 0

    def get_current_bbox_graph(self):
        nodes = nuke.allNodes(recurseGroups=True)
        if len(nodes) == 0: return 0, 0, 0, 0
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        for node in nodes:
            x = node.xpos()
            y = node.ypos()
            width = node.screenWidth()
            height = node.screenHeight()
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + width)
            max_y = max(max_y, y + height)
        self.__bbox_graph = min_x, min_y, max_x, max_y

    def __backdrop_data(self, backdrop_longname):
        backdrop_shortnames = backdrop_longname.split(".")
        nb_bd = len(backdrop_shortnames)
        current_bd = self.__backdrops_data
        for i, bd_sn in enumerate(backdrop_shortnames):
            if bd_sn not in current_bd["backdrops"]:
                parent_long_name = ".".join(backdrop_shortnames[:i])
                if len(parent_long_name) == 0: parent_long_name = None
                long_name = ".".join(backdrop_shortnames[:i + 1])
                current_bd["backdrops"][bd_sn] = LayoutManager.__get_init_backdrop_data(long_name, parent_long_name)
            current_bd = current_bd["backdrops"][bd_sn]
            if i == nb_bd - 1:
                return current_bd
        return None

    def add_nodes_to_backdrop(self, backdrop_longname, nodes=None):
        if nodes is None:
            nodes = []
        current_bd = self.__backdrop_data(backdrop_longname)
        for node in nodes:
            if node not in current_bd["nodes"]:
                current_bd["nodes"].append(node)

    def add_backdrop_option(self, backdrop_longname, option, value):
        current_bd = self.__backdrop_data(backdrop_longname)
        current_bd["options"][option] = value

    def add_top_level_backdrop_layout_relation(self, rel_backdrop_longname, backdrop_longname, position=POS_RIGHT,
                                               alignment=ALIGN_CENTER, mult_distance=1):
        self.__backdrops_layout_data[backdrop_longname] = {
            "base_backdrop": rel_backdrop_longname,
            "position": position,
            "alignment": alignment,
            "distance": mult_distance * _BASE_DISTANCE,
        }

    def add_node_layout_relation(self, base_node, node_to_place, position=POS_RIGHT, mult_distance=1):
        self.__nodes_layout_data[node_to_place] = {
            "base_node": base_node,
            "position": position,
            "distance": mult_distance * _BASE_DISTANCE,
            "visited": False
        }

    def build_layout_node_graph(self):
        def __build_layout_node_graph_aux(node_to_place):
            if node_to_place in self.__nodes_layout_data:
                lyt_rel = self.__nodes_layout_data[node_to_place]
                if lyt_rel["visited"]:
                    return
                lyt_rel["visited"] = True
                base_node = lyt_rel["base_node"]
                __build_layout_node_graph_aux(base_node)
                position = lyt_rel["position"]
                distance = lyt_rel["distance"]
                base_node_x = base_node.xpos()
                base_node_y = base_node.ypos()
                base_node_w = base_node.screenWidth()
                base_node_h = base_node.screenHeight()

                base_node_cx = base_node_x + base_node_w / 2.0
                base_node_cy = base_node_y + base_node_h / 2.0
                if position in [LayoutManager.POS_TOP, LayoutManager.POS_BOTTOM]:
                    node_to_place_x = base_node_cx
                elif position in [LayoutManager.POS_TOP_RIGHT, LayoutManager.POS_RIGHT, LayoutManager.POS_BOTTOM_RIGHT]:
                    node_to_place_x = base_node_cx + distance
                else:  # POS_BOTTOM_LEFT, POS_LEFT, POS_TOP_LEFT
                    node_to_place_x = base_node_cx - distance

                if position in [LayoutManager.POS_RIGHT, LayoutManager.POS_LEFT]:
                    node_to_place_y = base_node_cy
                elif position in [LayoutManager.POS_TOP, LayoutManager.POS_TOP_RIGHT, LayoutManager.POS_TOP_LEFT]:
                    node_to_place_y = base_node_cy - distance
                else:  # POS_BOTTOM_RIGHT, POS_BOTTOM, POS_BOTTOM_LEFT
                    node_to_place_y = base_node_cy + distance
                node_to_place_x -= node_to_place.screenWidth() / 2.0
                node_to_place_y -= node_to_place.screenHeight() / 2.0
                node_to_place.setXpos(int(node_to_place_x))
                node_to_place.setYpos(int(node_to_place_y))
            else:
                node_to_place.setXpos(0)
                node_to_place.setYpos(0)

        for node in self.__nodes_layout_data.keys():
            node.screenWidth(), node.screenHeight()
            __build_layout_node_graph_aux(node)

    def __compute_build_layout_backdrops(self):
        def __compute_build_layout_backdrop(bd_data):
            backdrops = bd_data["backdrops"]
            nodes = bd_data["nodes"]
            options = bd_data["options"]
            not_displayed = "display" in options and not options["display"]
            font_size = options["font_size"] if "font_size" in options else _DEFAULT_FONT_SIZE_BACKDROP
            margin_left = options["margin_left"] if "margin_left" in options else _MARGIN_BACKDROP[0]
            margin_top = options["margin_top"] if "margin_top" in options else _MARGIN_BACKDROP[1]
            margin_right = options["margin_right"] if "margin_right" in options else _MARGIN_BACKDROP[2]
            margin_bottom = options["margin_bottom"] if "margin_bottom" in options else _MARGIN_BACKDROP[3]
            if len(backdrops) == 0 and len(nodes) == 0:
                if not_displayed:
                    bd_x = bd_y = bd_x2 = bd_y2 = 0
                else:
                    bd_x, bd_y, bd_x2, bd_y2 = margin_left, margin_top, margin_right, margin_bottom
            else:
                bd_x = bd_y = bd_x2 = bd_y2 = None
                # NODES
                for node in nodes:
                    n_x = node.xpos()
                    n_y = node.ypos()
                    n_x2 = n_x + node.screenWidth()
                    n_y2 = n_y + node.screenHeight()
                    if bd_x > n_x or bd_x is None: bd_x = n_x
                    if bd_y > n_y or bd_y is None: bd_y = n_y
                    if bd_x2 < n_x2 or bd_x2 is None: bd_x2 = n_x2
                    if bd_y2 < n_y2 or bd_y2 is None: bd_y2 = n_y2
                # CHILDREN BACKDROPS
                for child_bd_data in backdrops.values():
                    child_bd_x, child_bd_y, child_bd_w, child_bd_h = __compute_build_layout_backdrop(child_bd_data)
                    child_bd_x2 = child_bd_x + child_bd_w
                    child_bd_y2 = child_bd_y + child_bd_h
                    if bd_x > child_bd_x or bd_x is None: bd_x = child_bd_x
                    if bd_y > child_bd_y or bd_y is None: bd_y = child_bd_y
                    if bd_x2 < child_bd_x2 or bd_x2 is None: bd_x2 = child_bd_x2
                    if bd_y2 < child_bd_y2 or bd_y2 is None: bd_y2 = child_bd_y2
                if not not_displayed:
                    bd_x -= margin_left
                    bd_y -= margin_top + font_size
                    bd_x2 += margin_right
                    bd_y2 += margin_bottom
            bd_w = bd_x2 - bd_x
            bd_h = bd_y2 - bd_y
            bd_data["layout_data"] = {
                "width": bd_w,
                "height": bd_h,
                "xpos": bd_x,
                "ypos": bd_y
            }
            return bd_x, bd_y, bd_w, bd_h

        for bd_data in self.__backdrops_data["backdrops"].values():
            __compute_build_layout_backdrop(bd_data)

    def __compute_top_level_backdrops_relation(self):
        def __translate_backdrop(tr_x, tr_y, bd_data):
            backdrops = bd_data["backdrops"]
            nodes = bd_data["nodes"]
            bd_data["layout_data"]["xpos"] += tr_x
            bd_data["layout_data"]["ypos"] += tr_y
            for child_bd_data in backdrops.values():
                __translate_backdrop(tr_x, tr_y, child_bd_data)
            for node in nodes:
                node.setXpos(int(node.xpos() + tr_x))
                node.setYpos(int(node.ypos() + tr_y))

        def __compute_backdrops_relation_aux(bd_longname, bd_lyt_data):
            bd_data = self.__backdrop_data(bd_longname)
            if "layout_data" not in bd_data: return
            base_bd_longname = bd_lyt_data["base_backdrop"]
            base_bd_data = self.__backdrop_data(base_bd_longname)
            if "layout_data" not in base_bd_data: return

            bd_layout_data = bd_data["layout_data"]
            base_bd_layout_data = base_bd_data["layout_data"]
            bd_x, bd_y = bd_layout_data["xpos"], bd_layout_data["ypos"]
            bd_w, bd_h = bd_layout_data["width"], bd_layout_data["height"]
            base_bd_x, base_bd_y = base_bd_layout_data["xpos"], base_bd_layout_data["ypos"]
            base_bd_w, base_bd_h = base_bd_layout_data["width"], base_bd_layout_data["height"]

            position = bd_lyt_data["position"]
            distance = bd_lyt_data["distance"]
            alignment = bd_lyt_data["alignment"]
            if alignment is LayoutManager.ALIGN_START:
                factor_align = 0
            elif alignment is LayoutManager.ALIGN_END:
                factor_align = 1
            else:  # ALIGN_CENTER
                factor_align = 1.0 / 2

            if position in [LayoutManager.POS_TOP, LayoutManager.POS_BOTTOM]:
                new_x = base_bd_x + (base_bd_w - bd_w) * factor_align
            elif position in [LayoutManager.POS_TOP_RIGHT, LayoutManager.POS_RIGHT, LayoutManager.POS_BOTTOM_RIGHT]:
                new_x = base_bd_x + base_bd_w + distance
            else:  # POS_BOTTOM_LEFT, POS_LEFT, POS_TOP_LEFT
                new_x = base_bd_x - bd_w - distance

            if position in [LayoutManager.POS_RIGHT, LayoutManager.POS_LEFT]:
                new_y = base_bd_y + (base_bd_h - bd_h) * factor_align
            elif position in [LayoutManager.POS_TOP, LayoutManager.POS_TOP_RIGHT, LayoutManager.POS_TOP_LEFT]:
                new_y = base_bd_y - bd_h - distance
            else:  # POS_BOTTOM_RIGHT, POS_BOTTOM, POS_BOTTOM_LEFT
                new_y = base_bd_y + base_bd_h + distance

            __translate_backdrop(new_x - bd_x, new_y - bd_y, bd_data)

        for bd_longname, bd_lyt_data in self.__backdrops_layout_data.items():
            __compute_backdrops_relation_aux(bd_longname, bd_lyt_data)

        bbox_x, bbox_y, bbox_x2, bbox_y2 = self.__bbox_graph

        tr_x = 0
        if bbox_x2 - bbox_x != 0:
            for bd_data in self.__backdrops_data["backdrops"].values():
                layout_data = bd_data["layout_data"]
                xpos, ypos = layout_data["xpos"], layout_data["ypos"]
                xpos2, ypos2 = xpos + layout_data["width"], ypos + layout_data["height"]
                if xpos < bbox_x2 and xpos2 > bbox_x and ypos < bbox_y2 and ypos2 > bbox_y:
                    new_tr_x = bbox_x2 - xpos
                    if new_tr_x > tr_x: tr_x = new_tr_x

            if tr_x != 0:
                print(tr_x)
                for bd_data in self.__backdrops_data["backdrops"].values():
                    __translate_backdrop(tr_x, 0, bd_data)

    def build_layout_backdrops(self):
        def __build_backdrop_node(backdrop_name, backdrop_data, z_order):
            for child_bd_name, child_bd_data in backdrop_data["backdrops"].items():
                __build_backdrop_node(child_bd_name, child_bd_data, z_order + 1)
            if "layout_data" not in backdrop_data:
                return
            layout_data = backdrop_data["layout_data"]
            options = backdrop_data["options"]
            if "display" in options and not options["display"]:
                return
            font_size = options["font_size"] if "font_size" in options else _DEFAULT_FONT_SIZE_BACKDROP
            color = options["color"] if "color" in options else _DEFAULT_COLOR_BACKDROP
            return nuke.nodes.BackdropNode(name=backdrop_name,
                                           xpos=int(layout_data["xpos"]), ypos=int(layout_data["ypos"]),
                                           bdwidth=layout_data["width"], bdheight=layout_data["height"],
                                           z_order=z_order,
                                           label=backdrop_name,
                                           note_font_size=font_size,
                                           tile_color=(color[0] << 24) | (color[1] << 16) | (color[2] << 8) | 255)

        self.__compute_build_layout_backdrops()
        self.__compute_top_level_backdrops_relation()
        __build_backdrop_node("", self.__backdrops_data, 0)

    def translate_graph_created(self):
        pass
