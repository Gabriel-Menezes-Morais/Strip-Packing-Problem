# Cutting & Packing Verification Tool (NFP)

This project is a computational tool designed to validate **2D Nesting (Cutting & Packing)** problems.

The system verifies the allocation of irregular convex polygons within a fixed-height, infinite-length strip, ensuring that parts do not overlap and respect the boundaries of the workspace. The geometric verification is based on the **No-Fit Polygon (NFP)** concept and the application of the **D-Function** (Cross Product).

## 📋 Features

* **Flexible Geometry:** Support for defining multiple types of convex polygons.
* **Inventory Management:** Tracks the number of available copies for each polygon type.
* **Boundary Validation:** Ensures the entire part is contained within the strip height ($H$) and that $X \ge 0$.
* **Robust Collision Detection:** Uses NFP matrices to mathematically determine if a new part invades the area of previously allocated parts.

---

## 🚀 Usage Guide (Data Input)

The program operates via the console (CLI). Due to the geometric nature of the problem, the **formatting and order of data** are crucial for correct operation.

### ⚠️ Golden Rule: Counter-Clockwise (CCW)

When entering vertex coordinates for any polygon (whether a piece or an NFP), you **MUST** follow a sequential **Counter-Clockwise** order.



* **Correct:** `(0,0) -> (10,0) -> (10,10) -> (0,10)`
* **Incorrect (Clockwise):** `(0,0) -> (0,10) -> (10,10) -> (10,0)`

> **Why does this matter?** The D-Function algorithm relies on vector orientation. If you use clockwise order, the math inverts the sign, causing the program to interpret "inside" as "outside," leading to severe collision errors.

### Coordinate Format

Whenever the program requests a coordinate, type the X and Y values separated by a single space.

* Example: `15 30` (Reads as: $x=15, y=30$)

### Execution Workflow

The data flow strictly follows this order:

#### 1. Global Configuration
1.  **Strip Height:** The maximum height of the sheet/strip.
2.  **Number of Types:** How many different polygon models exist in the problem.

#### 2. Polygon Type Definition
For each Type ($i$), the system will ask for:
1.  **Number of vertices.**
2.  **Number of copies.**
3.  **Vertices:** Enter them one by one (remember CCW). The first vertex is usually the local reference $(0,0)$.
4.  **Test Positions:** Enter the $(x, y)$ coordinates where you *plan* to place each copy. The system stores this to validate later.

#### 3. NFP Matrix Configuration


The NFP (No-Fit Polygon) defines the forbidden region. For every pair of polygons (Fixed Part $i$ vs. Mobile Part $j$), you must provide the resulting NFP polygon.
* If you have 2 polygon types, you will need to define 4 NFPs: $(0,0), (0,1), (1,0), (1,1)$.

#### 4. Allocation Loop
The program enters an interactive mode:
1.  You choose the **Type** of the part.
2.  You choose which **Copy** (index of the pre-defined position) to use.
3.  The system calculates if the position is valid.

---

## 🧠 Mathematical Theory

### D-Function (Cross Product)

To verify if a point $P$ collides with a polygon, we use the cross product between the polygon edge $AB$ and point $P$. The formula is:

$$D = (x_B - x_A)(y_P - y_A) - (y_B - y_A)(x_P - x_A)$$

* If $D < 0$: The point is to the right of the edge (Outside).
* If $D \ge 0$: The point is to the left or on the edge (Inside/Collision).
    *(Assuming polygon is in counter-clockwise order)*

### Virtual NFP Translation

To save memory, we do not create a copy of the NFP for every position in the plane. We store the NFP at the origin $(0,0)$ and translate coordinates "On-the-fly" during execution:

$$RealVertex = NFPVertex + FixedPartPosition$$

This way, we check if the *New Part Position* falls inside the NFP translated by the *Allocated Part Position*.

---

## 📄 Input Example

Scenario: A strip of height 100 with a 10x10 square.

```text
100         (Strip Height)
1           (1 Polygon Type)
4           (Square has 4 vertices)
1           (1 copy available)
0 0         (Vertex 0)
10 0        (Vertex 1)
10 10       (Vertex 2)
0 10        (Vertex 3)
50 50       (Position I want to test: x=50, y=50)
...         (Proceeds to NFP definition...)