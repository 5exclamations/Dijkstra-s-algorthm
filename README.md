# Dijkstra's Path Explorer

Interactive Tkinter visualiser for Dijkstra's shortest-path algorithm. Draw a weighted graph on the canvas, pick a start node, then run the algorithm in one go or step by step. The panel shows the priority queue and the distance table as they change, and nodes and edges are coloured by state: in the queue, current, being relaxed, visited.

- Left-click to add nodes and connect them; right-click to change edge weights or delete nodes and edges
- Load a built-in example graph, or save and load graphs as JSON
- Implementation uses `heapq` as the priority queue

## Run

```bash
python3 dijkstra.py
```

Requires Python 3 with Tkinter (included in the standard python.org installers).
