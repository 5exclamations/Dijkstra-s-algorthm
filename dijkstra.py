import tkinter as tk
from tkinter import simpledialog, messagebox, font, filedialog
import heapq
import collections
import math
import json

NODE_RADIUS = 15
FONT_SIZE = 10


COLOR_DEFAULT = "gray"
COLOR_IN_PQ = "yellow"
COLOR_CURRENT = "blue"
COLOR_RELAXING = "green"
COLOR_VISITED = "black"
COLOR_TEXT_LIGHT = "white"
COLOR_TEXT_DARK = "black"
COLOR_EDGE_DEFAULT = "black"
COLOR_EDGE_HIGHLIGHT = "blue"


class DijkstraGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Dijkstra’s Path Explorer")
        self.root.geometry("1200x800")

        self.control_frame = tk.Frame(self.root, width=300, relief=tk.RIDGE, bd=2)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.control_frame.pack_propagate(False)

        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=1, highlightbackground="black")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._init_data_structures()

        self._setup_controls()

        self.canvas.bind("<Button-1>", self.on_canvas_left_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.selected_node_id = None
        self.node_name_counter = 0

    def _init_data_structures(self):
        self.graph = collections.defaultdict(list)
        self.nodes = {}
        self.edges = {}

        self.alg_running = False
        self.distances = {}
        self.previous = {}
        self.pq = []
        self.visited = set()

        self.alg_step_state = None
        self.current_node = None
        self.neighbors_to_process = []

    def _setup_controls(self):
        pad_y = 5
        pad_x = 10

        alg_frame = tk.LabelFrame(self.control_frame, text="Control", padx=pad_x, pady=pad_y)
        alg_frame.pack(fill=tk.X, padx=pad_x, pady=pad_y)

        tk.Label(alg_frame, text="Starting node:").pack(anchor=tk.W)
        self.start_node_entry = tk.Entry(alg_frame, width=10)
        self.start_node_entry.pack(fill=tk.X, pady=2)

        self.run_button = tk.Button(alg_frame, text="Run Dijkstra", command=self.run_dijkstra_full)
        self.run_button.pack(fill=tk.X, pady=pad_y)

        self.step_button = tk.Button(alg_frame, text="Step-by-Step", command=self.dijkstra_step)
        self.step_button.pack(fill=tk.X, pady=pad_y)

        self.reset_alg_button = tk.Button(alg_frame, text="Reset Algorithm",
                                          command=self.reset_algorithm_state)
        self.reset_alg_button.pack(fill=tk.X, pady=(pad_y, 0))

        graph_frame = tk.LabelFrame(self.control_frame, text="Graph", padx=pad_x, pady=pad_y)
        graph_frame.pack(fill=tk.X, padx=pad_x, pady=pad_y)

        self.load_example_button = tk.Button(graph_frame, text="Load Example Graph",
                                             command=self.load_example_graph)
        self.load_example_button.pack(fill=tk.X, pady=pad_y)

        file_frame = tk.Frame(graph_frame)
        file_frame.pack(fill=tk.X)
        self.save_graph_button = tk.Button(file_frame, text="Save Graph", command=self.save_graph_to_file)
        self.save_graph_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.load_graph_button = tk.Button(file_frame, text="Load Graph", command=self.load_graph_from_file)
        self.load_graph_button.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        self.reset_graph_button = tk.Button(graph_frame, text="Reset Graph", command=self.reset_graph,
                                            fg="red")
        self.reset_graph_button.pack(fill=tk.X, pady=(pad_y * 2, 0))

        output_frame = tk.LabelFrame(self.control_frame, text="Output", padx=pad_x, pady=pad_y)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=pad_x, pady=pad_y)

        tk.Label(output_frame, text="Priority queue:").pack(anchor=tk.W)
        self.pq_label = tk.Label(output_frame, text="[]", relief=tk.SUNKEN, wraplength=280, justify=tk.LEFT)
        self.pq_label.pack(fill=tk.X, pady=2)

        tk.Label(output_frame, text="Distance table:").pack(anchor=tk.W, pady=(10, 0))
        self.results_text = tk.Text(output_frame, height=20, font=("Courier New", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=pad_y)

        self.status_label = tk.Label(self.control_frame, text="Create a graph", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        self._update_results_table()


    def _get_next_node_name(self):
        name = ""
        n = self.node_name_counter
        while n >= 0:
            name = chr(ord('A') + n % 26) + name
            n = n // 26 - 1

        while name in self.nodes:
            self.node_name_counter += 1
            n = self.node_name_counter
            name = ""
            while n >= 0:
                name = chr(ord('A') + n % 26) + name
                n = n // 26 - 1

        self.node_name_counter += 1
        return name

    def _find_node_at(self, x, y):
        for name, data in self.nodes.items():
            dist_sq = (data['x'] - x) ** 2 + (data['y'] - y) ** 2
            if dist_sq <= NODE_RADIUS ** 2:
                return name
        return None

    def _find_edge_at(self, x, y):
        item_id = self.canvas.find_closest(x, y)[0]

        for edge_key, data in self.edges.items():
            if item_id in (data['id_text'], data['id_text_bg']):
                return edge_key
        return None

    def on_canvas_left_click(self, event):
        if self.alg_running:
            messagebox.showwarning("Error",
                                   "Can't change the graph while alghorithm is running. Press 'Reset Algorithm'.")
            return

        x, y = event.x, event.y
        clicked_node_name = self._find_node_at(x, y)

        if clicked_node_name:
            if self.selected_node_id is None:
                self.selected_node_id = clicked_node_name
                self._set_node_color(clicked_node_name, COLOR_CURRENT, COLOR_TEXT_LIGHT)
            elif self.selected_node_id == clicked_node_name:
                self._set_node_color(self.selected_node_id, COLOR_DEFAULT, COLOR_TEXT_DARK)
                self.selected_node_id = None
            else:
                node_a = self.selected_node_id
                node_b = clicked_node_name
                self._set_node_color(node_a, COLOR_DEFAULT, COLOR_TEXT_DARK)
                self.selected_node_id = None

                edge_key = tuple(sorted((node_a, node_b)))
                if edge_key in self.edges:
                    messagebox.showinfo("Info", f"Node between {node_a} and {node_b} already exists.")
                    return

                weight = simpledialog.askinteger("Node weight", f"Enter node weight {node_a} <-> {node_b}:",
                                                 minvalue=0)
                if weight is not None:
                    self.create_edge(node_a, node_b, weight)
                    self.graph[node_a].append((node_b, weight))
                    self.graph[node_b].append((node_a, weight))
                    self.reset_algorithm_state()
        else:
            if self.selected_node_id:
                self._set_node_color(self.selected_node_id, COLOR_DEFAULT, COLOR_TEXT_DARK)
                self.selected_node_id = None
            else:
                node_name = self._get_next_node_name()
                if node_name not in self.nodes:
                    self.create_node(x, y, node_name)
                    self.reset_algorithm_state()

    def on_canvas_right_click(self, event):
        if self.alg_running: return

        x, y = event.x, event.y

        clicked_node_name = self._find_node_at(x, y)
        if clicked_node_name:
            self.show_node_menu(event, clicked_node_name)
            return

        edge_key = self._find_edge_at(x, y)
        if edge_key:
            self.show_edge_menu(event, edge_key)


    def show_node_menu(self, event, node_name):
        menu = tk.Menu(self.canvas, tearoff=0)
        menu.add_command(label=f"Delete node ({node_name})", command=lambda: self.delete_node(node_name))
        menu.post(event.x_root, event.y_root)

    def delete_node(self, node_name):
        if node_name not in self.nodes: return

        keys_to_delete = [k for k in self.edges if node_name in k]
        for edge_key in keys_to_delete:
            self._delete_edge_logic(edge_key)


        if node_name in self.graph:
            del self.graph[node_name]

        node_data = self.nodes[node_name]
        self.canvas.delete(node_data['id_oval'])
        self.canvas.delete(node_data['id_text'])

        del self.nodes[node_name]

        if self.selected_node_id == node_name:
            self.selected_node_id = None

        self.status_label.config(text=f"Node {node_name} and connecting nodes are deleted.")
        self.reset_algorithm_state()

    def show_edge_menu(self, event, edge_key):
        u, v = edge_key
        menu = tk.Menu(self.canvas, tearoff=0)
        menu.add_command(label=f"Change weight({u}<->{v})", command=lambda: self.change_edge_weight(edge_key))
        menu.add_command(label=f"Delete edge ({u}<->{v})", command=lambda: self.delete_edge(edge_key))
        menu.post(event.x_root, event.y_root)

    def change_edge_weight(self, edge_key):
        u, v = edge_key
        old_weight = self.edges[edge_key]['weight']

        new_weight = simpledialog.askinteger(
            "Change weight",
            f"Enter new weight for node {u} <-> {v} (old: {old_weight}):",
            initialvalue=old_weight, minvalue=0
        )

        if new_weight is not None and new_weight != old_weight:
            try:
                self.graph[u].remove((v, old_weight))
                self.graph[v].remove((u, old_weight))
            except ValueError:
                pass

            self.graph[u].append((v, new_weight))
            self.graph[v].append((u, new_weight))

            # Обновляем холст
            self.canvas.itemconfig(self.edges[edge_key]['id_text'], text=str(new_weight))
            self.edges[edge_key]['weight'] = new_weight

            self.status_label.config(text=f"Weight {u}<->{v} changed to{new_weight}")
            self.reset_algorithm_state()

    def delete_edge(self, edge_key):
        self._delete_edge_logic(edge_key)
        self.status_label.config(text=f"Edge {edge_key[0]}<->{edge_key[1]} is deleted.")
        self.reset_algorithm_state()

    def _delete_edge_logic(self, edge_key):
        if edge_key not in self.edges: return

        u, v = edge_key
        weight = self.edges[edge_key]['weight']

        try:
            self.graph[u].remove((v, weight))
            self.graph[v].remove((u, weight))
        except ValueError:
            pass


        for item_id in (self.edges[edge_key]['id_line'], self.edges[edge_key]['id_text'],
                        self.edges[edge_key]['id_text_bg']):
            self.canvas.delete(item_id)

        del self.edges[edge_key]

    def create_node(self, x, y, name):

        oval_id = self.canvas.create_oval(
            x - NODE_RADIUS, y - NODE_RADIUS,
            x + NODE_RADIUS, y + NODE_RADIUS,
            fill=COLOR_DEFAULT, outline="black", width=2, tags="node"
        )
        text_id = self.canvas.create_text(x, y, text=name, fill=COLOR_TEXT_DARK, font=("Arial", FONT_SIZE, "bold"),
                                          tags="node_text")
        self.nodes[name] = {'id_oval': oval_id, 'id_text': text_id, 'x': x, 'y': y}

    def create_edge(self, node_a, node_b, weight):

        edge_key = tuple(sorted((node_a, node_b)))
        if edge_key in self.edges: return

        data_a = self.nodes[node_a]
        data_b = self.nodes[node_b]

        line_id = self.canvas.create_line(
            data_a['x'], data_a['y'], data_b['x'], data_b['y'],
            fill=COLOR_EDGE_DEFAULT, width=2, tags="edge"
        )
        self.canvas.tag_raise("node")
        self.canvas.tag_raise("node_text")

        mid_x, mid_y = (data_a['x'] + data_b['x']) / 2, (data_a['y'] + data_b['y']) / 2


        text_bg_id = self.canvas.create_rectangle(
            mid_x - 10, mid_y - 8, mid_x + 10, mid_y + 8,
            fill="white", outline="white", tags="edge_text_bg"
        )

        text_id = self.canvas.create_text(mid_x, mid_y, text=str(weight), fill="black", font=("Arial", FONT_SIZE - 1),
                                          tags="edge_text")

        self.edges[edge_key] = {
            'id_line': line_id,
            'id_text': text_id,
            'id_text_bg': text_bg_id,
            'weight': weight
        }

    def _set_buttons_state(self, state):
        self.run_button.config(state=state)
        self.step_button.config(state=tk.NORMAL if state == tk.DISABLED else tk.NORMAL)
        self.start_node_entry.config(state=state)
        self.load_example_button.config(state=state)
        self.load_graph_button.config(state=state)
        self.save_graph_button.config(state=state)
        self.reset_graph_button.config(state=state)

    def _start_algorithm(self):
        start_node = self.start_node_entry.get().strip().upper()
        if start_node not in self.nodes:
            messagebox.showerror("Error", f"Node '{start_node}' is not found on graph")
            return False

        self.reset_algorithm_state(clear_canvas=True)
        self.alg_running = True

        self.distances = {node: math.inf for node in self.nodes}
        self.previous = {node: None for node in self.nodes}
        self.pq = []
        self.visited = set()

        self.distances[start_node] = 0
        heapq.heappush(self.pq, (0, start_node))

        self._set_node_color(start_node, COLOR_IN_PQ, COLOR_TEXT_DARK)
        self._set_buttons_state(tk.DISABLED)
        self.reset_alg_button.config(state=tk.NORMAL)

        self.alg_step_state = 'pop'
        self.status_label.config(text=f"Algorithm is running. {start_node} = 0. Ready to be out.")
        self._update_all_gui()
        return True

    def _finish_algorithm(self):
        self.alg_running = False
        self.alg_step_state = None
        self._set_buttons_state(tk.NORMAL)
        self.reset_alg_button.config(state=tk.DISABLED)
        self.status_label.config(text="Algorithm is running.")
        messagebox.showinfo("Finished", "Algorithm has finished its work.")

    def reset_algorithm_state(self, clear_canvas=True):
        self.alg_running = False
        self.alg_step_state = None
        self.current_node = None
        self.neighbors_to_process = []

        self._set_buttons_state(tk.NORMAL)
        self.reset_alg_button.config(state=tk.DISABLED)
        self.status_label.config(text="Ready to run.")

        if clear_canvas:
            for node_name in self.nodes:
                self._set_node_color(node_name, COLOR_DEFAULT, COLOR_TEXT_DARK)
            for edge_key in self.edges:
                self._set_edge_color(edge_key, COLOR_EDGE_DEFAULT)

        self.distances = {node: math.inf for node in self.nodes}
        self.previous = {node: None for node in self.nodes}
        self.pq = []
        self.visited = set()
        self._update_all_gui()

    def reset_graph(self):
        self.canvas.delete("all")
        self._init_data_structures()
        self.selected_node_id = None
        self.node_name_counter = 0
        self.reset_algorithm_state(clear_canvas=False)
        self.start_node_entry.delete(0, tk.END)
        self.status_label.config(text="Graph is cleared.")

    def run_dijkstra_full(self):
        if self.alg_running: return
        if not self._start_algorithm(): return

        self.root.after(500, self._animate_step)

    def _animate_step(self):
        if not self.alg_running: return

        self.dijkstra_step()

        if self.alg_running:
            self.root.after(500, self._animate_step)

    def dijkstra_step(self):

        if not self.alg_running:
            if not self._start_algorithm():
                return
            return

        self._reset_transient_colors()

        if self.alg_step_state == 'pop':
            if not self.pq:
                self._finish_algorithm()
                return

            # Searching for next unvisited node
            current_distance, node = -1, None
            while self.pq:
                current_distance, node = heapq.heappop(self.pq)
                if node not in self.visited:
                    break

            if node is None or node in self.visited:
                self._finish_algorithm()
                return

            self.current_node = node
            self.visited.add(self.current_node)

            self._set_node_color(self.current_node, COLOR_CURRENT, COLOR_TEXT_LIGHT)
            self.status_label.config(text=f"Извлечен: {self.current_node} (d={current_distance})")

            self.neighbors_to_process = list(self.graph[self.current_node])
            self.alg_step_state = 'relax'

        elif self.alg_step_state == 'relax':

            if not self.neighbors_to_process:
                self._set_node_color(self.current_node, COLOR_VISITED, COLOR_TEXT_LIGHT)
                self.status_label.config(text=f"Finished: {self.current_node}. Ready to be out.")
                self.alg_step_state = 'pop'
                self._update_all_gui()
                return

            neighbor, weight = self.neighbors_to_process.pop(0)

            if neighbor in self.visited:
                self.status_label.config(text=f"Update: {neighbor} has already been visited. Pass.")
                self._update_all_gui()
                return

            new_distance = self.distances[self.current_node] + weight

            self._set_node_color(neighbor, COLOR_RELAXING, COLOR_TEXT_DARK)
            edge_key = tuple(sorted((self.current_node, neighbor)))
            self._set_edge_color(edge_key, COLOR_EDGE_HIGHLIGHT)

            if new_distance < self.distances[neighbor]:
                self.distances[neighbor] = new_distance
                self.previous[neighbor] = self.current_node
                heapq.heappush(self.pq, (new_distance, neighbor))
                self.status_label.config(text=f"Update: {neighbor} (d={new_distance})")
            else:
                self.status_label.config(text=f"Update: {neighbor} (Route is not shorter). Pass.")

        self._update_all_gui()

    def _reset_transient_colors(self):
        for node_name in self.nodes:
            if node_name == self.current_node and self.alg_step_state == 'relax':
                self._set_node_color(node_name, COLOR_CURRENT, COLOR_TEXT_LIGHT)
            elif node_name in self.visited:
                self._set_node_color(node_name, COLOR_VISITED, COLOR_TEXT_LIGHT)
            elif self.distances.get(node_name, math.inf) != math.inf:
                self._set_node_color(node_name, COLOR_IN_PQ, COLOR_TEXT_DARK)
            else:
                self._set_node_color(node_name, COLOR_DEFAULT, COLOR_TEXT_DARK)

        for edge_key in self.edges:
            self._set_edge_color(edge_key, COLOR_EDGE_DEFAULT)


    def _update_all_gui(self):
        self._update_results_table()
        self._update_pq_display()

    def _update_results_table(self):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        header = f"{'Node':<6} | {'Dist':<8} | {'Prev':<6}\n"
        self.results_text.insert(tk.END, header)
        self.results_text.insert(tk.END, "-" * (len(header) - 1) + "\n")

        if not self.distances:
            self.results_text.insert(tk.END, "Algorithm is not running.")
            self.results_text.config(state=tk.DISABLED)
            return

        sorted_nodes = sorted(self.distances.keys())
        for node in sorted_nodes:
            dist = self.distances[node]
            dist_str = "inf" if dist == math.inf else f"{dist:.0f}"
            prev_str = self.previous.get(node) or "-"

            line = f"{node:<6} | {dist_str:<8} | {prev_str:<6}\n"
            self.results_text.insert(tk.END, line)

        self.results_text.config(state=tk.DISABLED)

    def _update_pq_display(self):
        #update of queue
        pq_copy = sorted([item for item in self.pq if item[1] not in self.visited])
        pq_str = ", ".join([f"({d}, '{n}')" for d, n in pq_copy])
        self.pq_label.config(text=f"[{pq_str}]")

    def _set_node_color(self, node_name, fill_color, text_color):
        if node_name in self.nodes:
            data = self.nodes[node_name]
            self.canvas.itemconfig(data['id_oval'], fill=fill_color)
            self.canvas.itemconfig(data['id_text'], fill=text_color)

    def _set_edge_color(self, edge_key, color):
        if edge_key and edge_key in self.edges:
            data = self.edges[edge_key]
            self.canvas.itemconfig(data['id_line'], fill=color)


    def load_example_graph(self):
        self.reset_graph()

        pos = {
            'A': (100, 150), 'B': (250, 100), 'C': (250, 200),
            'D': (400, 150), 'E': (550, 150), 'F': (400, 250)
        }
        edges = [
            ('A', 'B', 7), ('A', 'C', 9),
            ('B', 'C', 10), ('B', 'D', 15),
            ('C', 'D', 11), ('C', 'F', 2),
            ('D', 'E', 6),
            ('F', 'E', 9)
        ]

        for name, (x, y) in pos.items():
            self.create_node(x, y, name)

        for u, v, weight in edges:
            self.create_edge(u, v, weight)
            self.graph[u].append((v, weight))
            self.graph[v].append((u, weight))

        self.node_name_counter = len(pos)  # counter update
        self.status_label.config(text="Example graph is running")
        self.reset_algorithm_state(clear_canvas=False)

    def save_graph_to_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath: return

        try:
            nodes_data = {name: {"x": data['x'], "y": data['y']} for name, data in self.nodes.items()}
            edges_data = [[u, v, data['weight']] for (u, v), data in self.edges.items()]

            data = {"nodes": nodes_data, "edges": edges_data}

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.status_label.config(text=f"Graph is saved in {filepath}")
        except Exception as e:
            messagebox.showerror("Save error", f"Couldn't save the graph: {e}")

    def load_graph_from_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath: return

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.reset_graph()

            for name, pos in data["nodes"].items():
                self.create_node(pos['x'], pos['y'], name)

            for u, v, weight in data["edges"]:
                if u in self.nodes and v in self.nodes:
                    self.create_edge(u, v, weight)
                    self.graph[u].append((v, weight))
                    self.graph[v].append((u, weight))

            self.node_name_counter = len(data["nodes"])
            self.status_label.config(text=f"Graph is loaded from{filepath}")
            self.reset_algorithm_state(clear_canvas=False)

        except Exception as e:
            messagebox.showerror("Load error", f"Couldn't load the graph {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DijkstraGUI(root)
    root.mainloop()