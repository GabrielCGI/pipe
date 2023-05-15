import nuke
from common.utils import *

# ######################################################################################################################

_MARGIN_BACKDROP = (20, 20, 20, 20)
_DEFAULT_FONT_SIZE_BACKDROP = 30
_DEFAULT_COLOR_BACKDROP = (150, 150, 150)
_DEFAULT_LAYOUT_BACKDROP = "v"

_NODE_WIDTH = 80
_NODE_HEIGHT = 66
_BASE_DISTANCE_NODES = 20
_BASE_DISTANCE_BACKDROPS = 40
# _NODE_GRAPH_WORKSPACE_POS_Y = -100000
# _NODE_GRAPH_WORKSPACE_INCR_Y = 10000
_NODE_GRAPH_WORKSPACE_MARGIN_X = 1000

_NODE_GRAPH_WORKSPACE_POS_Y = -1000  # TODO
_NODE_GRAPH_WORKSPACE_INCR_Y = 500


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
    ALIGN_TOP = 1
    ALIGN_RIGHT = 2
    ALIGN_BOTTOM = 3
    ALIGN_LEFT = 4
    ALIGN_CENTER = 5

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

    @staticmethod
    def __get_bbox_graph():
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
        return min_x, min_y, max_x, max_y

    def __init__(self):
        self.__backdrops_data = LayoutManager.__get_init_backdrop_data("", None)
        self.__nodes_layout_data = {}
        self.__current_workspace_y = None

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

    def add_backdrop_layout_relation(self, rel_backdrop_longname, backdrop_longname, position=POS_RIGHT,
                                     alignment=ALIGN_CENTER, mult_distance=1):
        current_bd = self.__backdrop_data(backdrop_longname)
        current_bd["relation"] = {
            "base_backdrop": rel_backdrop_longname,
            "position": position,
            "alignment": alignment,
            "distance": mult_distance * _BASE_DISTANCE_BACKDROPS,
        }

    def add_node_layout_relation(self, base_node, node_to_place, position=POS_RIGHT, mult_distance=1):
        self.__nodes_layout_data[node_to_place] = {
            "base_node": base_node,
            "position": position,
            "distance": mult_distance * _BASE_DISTANCE_NODES,
            "visited": False
        }

    def build_layout_node_graph(self):
        def __build_layout_node_graph_aux(node_to_place, workspace_x):
            if node_to_place in self.__nodes_layout_data:
                lyt_rel = self.__nodes_layout_data[node_to_place]
                if lyt_rel["visited"]:
                    return
                lyt_rel["visited"] = True
                base_node = lyt_rel["base_node"]
                __build_layout_node_graph_aux(base_node, workspace_x)
                position = lyt_rel["position"]
                distance = lyt_rel["distance"]
                base_node_x = base_node.xpos()
                base_node_y = base_node.ypos()
                base_node_w = base_node.screenWidth()
                base_node_h = base_node.screenHeight()
                if position in [LayoutManager.POS_TOP, LayoutManager.POS_BOTTOM]:
                    node_to_place_x = base_node_x + (base_node_w - node_to_place.screenWidth()) / 2
                else:
                    x_padding = (_NODE_WIDTH - base_node_w) / 2
                    if position in [LayoutManager.POS_TOP_RIGHT, LayoutManager.POS_RIGHT,
                                    LayoutManager.POS_BOTTOM_RIGHT]:
                        node_to_place_x = base_node_x + x_padding + base_node_w + distance
                    else:  # POS_BOTTOM_LEFT, POS_LEFT, POS_TOP_LEFT
                        node_to_place_x = base_node_x - x_padding - _NODE_WIDTH - distance

                if position in [LayoutManager.POS_RIGHT, LayoutManager.POS_LEFT]:
                    node_to_place_y = base_node_y + (base_node_h - node_to_place.screenHeight()) / 2
                else:
                    y_padding = (_NODE_HEIGHT - base_node_h) / 2
                    if position in [LayoutManager.POS_TOP, LayoutManager.POS_TOP_RIGHT, LayoutManager.POS_TOP_LEFT]:
                        node_to_place_y = base_node_y - y_padding - _NODE_HEIGHT - distance
                    else:  # POS_BOTTOM_RIGHT, POS_BOTTOM, POS_BOTTOM_LEFT
                        node_to_place_y = base_node_y + y_padding + base_node_h + distance
                node_to_place.setXpos(node_to_place_x)
                node_to_place.setYpos(node_to_place_y)
            else:
                node_to_place.setXpos(int(workspace_x))
                node_to_place.setYpos(self.__current_workspace_y)
                self.__current_workspace_y += _NODE_GRAPH_WORKSPACE_INCR_Y

        bbox = self.__get_bbox_graph()
        self.__current_workspace_y = _NODE_GRAPH_WORKSPACE_POS_Y
        workspace_x = bbox[2] + _NODE_GRAPH_WORKSPACE_MARGIN_X
        for node in self.__nodes_layout_data.keys():
            node.screenWidth()
            node.screenHeight()
            __build_layout_node_graph_aux(node, workspace_x)

    def __compute_build_layout_backdrops(self):
        def __translate_backdrop(tr_x, tr_y, bd_longname, bd_data=None):
            if bd_data is None:
                bd_data = self.__backdrop_data(bd_longname)
            if bd_longname is None:
                bd_longname = bd_data["long_name"]
            print("tr", bd_longname, tr_x, tr_y)
            backdrops = bd_data["backdrops"]
            nodes = bd_data["nodes"]
            for child_bd_data in backdrops.values():
                __translate_backdrop(tr_x, tr_y, None, child_bd_data)
            for node in nodes:
                node.setXpos(node.xpos() + tr_x)
                node.setYpos(node.ypos() + tr_y)

        def __compute_build_layout_backdrop(bd_longname, bd_data=None, searching_for = "pos"):
            # Retrieve data and name if not available
            if bd_data is None:
                bd_data = self.__backdrop_data(bd_longname)
            if bd_longname is None:
                bd_longname = bd_data["long_name"]


            bd_parent_longname = bd_data["parent_long_name"]
            backdrops = bd_data["backdrops"]
            nodes = bd_data["nodes"]
            options = bd_data["options"]
            font_size = options["font_size"] if "font_size" in options else _DEFAULT_FONT_SIZE_BACKDROP
            relation = bd_data["relation"]

            print("comp", bd_longname, bd_parent_longname)

            x = None
            y = None
            w = None
            h = None
            has_bounds = "layout_bounds" in bd_data
            has_pos = "layout_pos" in bd_data

            return_now = False
            if has_bounds:
                layout_bounds = bd_data["layout_bounds"]
                w = layout_bounds["width"]
                h = layout_bounds["height"]
            if has_pos:
                layout_pos = bd_data["layout_pos"]
                x = layout_pos["xpos"]
                y = layout_pos["ypos"]
            if (has_bounds and searching_for is "bounds") or \
                    (has_pos and searching_for is "pos") or \
                    ((has_bounds or has_pos) and searching_for is "both"):
                return x, y, w, h

            if relation is None:
                if bd_parent_longname is None:
                    # bbox = LayoutManager.__get_bbox_graph() #TODO
                    # x = bbox[0]
                    # y = bbox[1]
                    x = 0
                    y = 0
                else:
                    # If has parent compute the position thanks to the parent position
                    prt_bd_x, prt_bd_y, prt_bd_w, prt_bd_h = __compute_build_layout_backdrop(bd_parent_longname,searching_for="pos")
                    print(bd_parent_longname+ " is at "+ str(prt_bd_x)+" "+str(prt_bd_y))
                    x = prt_bd_x + _MARGIN_BACKDROP[0]
                    y = prt_bd_y + _MARGIN_BACKDROP[1]
                print("set pos of "+bd_longname+ " to "+str(x)+" "+str(y))
                bd_data["layout_pos"] = {
                    "xpos": x,
                    "ypos": y
                }

            if len(backdrops) == 0 and len(nodes) == 0:
                bd_x = _MARGIN_BACKDROP[0]
                bd_y = _MARGIN_BACKDROP[1]
                bd_x2 = _MARGIN_BACKDROP[2]
                bd_y2 = _MARGIN_BACKDROP[3]
            else:
                bd_x = None
                bd_y = None
                bd_x2 = None
                bd_y2 = None
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
                    child_bd_x, child_bd_y, child_bd_w, child_bd_h = __compute_build_layout_backdrop(None,
                                                                                                     child_bd_data,
                                                                                                     searching_for="bounds")
                    child_bd_x2 = child_bd_x + child_bd_w
                    child_bd_y2 = child_bd_y + child_bd_h
                    if bd_x > child_bd_x or bd_x is None: bd_x = child_bd_x
                    if bd_y > child_bd_y or bd_y is None: bd_y = child_bd_y
                    if bd_x2 < child_bd_x2 or bd_x2 is None: bd_x2 = child_bd_x2
                    if bd_y2 < child_bd_y2 or bd_y2 is None: bd_y2 = child_bd_y2
                bd_x -= _MARGIN_BACKDROP[0]
                bd_y -= _MARGIN_BACKDROP[1]
                bd_x2 += _MARGIN_BACKDROP[2]
                bd_y2 += _MARGIN_BACKDROP[3]
                print(str(bd_longname), "bb", bd_x, bd_y, bd_x2, bd_y2)
            bd_w = bd_x2 - bd_x
            bd_h = bd_y2 - bd_y
            print("set bounds of "+bd_longname+ " to "+str(bd_w)+" "+str(bd_h))
            bd_data["layout_bounds"] = {
                "width": bd_w,
                "height": bd_h,
            }


            # RELATION
            if relation is not None:
                base_bd = relation["base_backdrop"]
                distance = relation["distance"]
                position = relation["position"]
                alignment = relation["alignment"]  # TODO
                print("b")
                base_bd_x, base_bd_y, base_bd_w, base_bd_h = __compute_build_layout_backdrop(base_bd)

                if position in [LayoutManager.POS_TOP, LayoutManager.POS_BOTTOM]:
                    x = base_bd_x + (base_bd_w - bd_w) / 2
                else:
                    x_padding = (bd_w - base_bd_w) / 2
                    if position in [LayoutManager.POS_TOP_RIGHT, LayoutManager.POS_RIGHT,
                                    LayoutManager.POS_BOTTOM_RIGHT]:
                        x = base_bd_x + x_padding + base_bd_w + distance
                    else:  # POS_BOTTOM_LEFT, POS_LEFT, POS_TOP_LEFT
                        x = base_bd_x - x_padding - bd_w - distance

                if position in [LayoutManager.POS_RIGHT, LayoutManager.POS_LEFT]:
                    y = base_bd_y + (base_bd_h - bd_h) / 2
                else:
                    y_padding = (bd_h - base_bd_h) / 2
                    if position in [LayoutManager.POS_TOP, LayoutManager.POS_TOP_RIGHT, LayoutManager.POS_TOP_LEFT]:
                        y = base_bd_y - y_padding - bd_h - distance
                    else:  # POS_BOTTOM_RIGHT, POS_BOTTOM, POS_BOTTOM_LEFT
                        y = base_bd_y + y_padding + base_bd_h + distance

                bd_data["layout_pos"] = {
                    "xpos": x - bd_x,
                    "ypos": y - bd_y
                }

            __translate_backdrop(x - bd_x, y - bd_y, bd_longname, bd_data)
            return x, y, bd_w, bd_h

        for bd_longname, bd_data in self.__backdrops_data["backdrops"].items():
            a, b, c, d = __compute_build_layout_backdrop(bd_longname, bd_data)
            # print(bd_longname, a, b, c, d)


    def build_layout_backdrops(self):
        def __build_backdrop_node(backdrop_name, backdrop_data, z_order):
            # nodes = backdrop_data["nodes"]
            for child_bd_name, child_bd_data in backdrop_data["backdrops"].items():
                # nodes.append(__build_backdrop(child_bd_name, child_bd_data, z_order + 1))
                __build_backdrop_node(child_bd_name, child_bd_data, z_order + 1)
            if backdrop_name is None or "layout_bounds" not in backdrop_data or "layout_pos" not in backdrop_data:
                return
            layout_bounds = backdrop_data["layout_bounds"]
            layout_pos = backdrop_data["layout_pos"]
            print_var(backdrop_name, layout_bounds, layout_pos)
            options = backdrop_data["options"]
            font_size = options["font_size"] if "font_size" in options else _DEFAULT_FONT_SIZE_BACKDROP
            color = options["color"] if "color" in options else _DEFAULT_COLOR_BACKDROP
            return nuke.nodes.BackdropNode(name=backdrop_name,
                                           xpos=layout_pos["xpos"], ypos=layout_pos["ypos"],
                                           bdwidth=layout_bounds["width"], bdheight=layout_bounds["height"],
                                           z_order=z_order,
                                           label=backdrop_name,
                                           note_font_size=font_size,
                                           tile_color=(color[0] << 24) | (color[1] << 16) | (color[2] << 8) | 255)

        self.__compute_build_layout_backdrops()
        __build_backdrop_node(None, self.__backdrops_data, 0)
