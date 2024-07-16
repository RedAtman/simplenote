from random import randint, shuffle


def empty_generator():
    return
    yield


def bstslice(tree, left, right):
    def inorder(node):
        if node.left and left < node.key:
            for kv in inorder(node.left):
                yield kv

        if node.key >= left and node.key <= right:
            yield (node.key, node.val)

        if node.right and right > node.key:
            for kv in inorder(node.right):
                yield kv

    if left == None or right == None or left > right:
        return []

    curr = tree._find_node_margin(tree.root, left)
    while curr:
        if curr.key >= left and curr.key <= right:
            yield (curr.key, curr.val)
            if curr.right:
                for kv in inorder(curr.right):
                    yield kv

        curr = curr.parent


class bstnode:
    key: any
    val: any
    parent: "bstnode"
    left: "bstnode"
    right: "bstnode"

    def depth(self):
        return 1 + max(self.left.depth() if self.left else 0, self.right.depth() if self.right else 0)

    def inorder(self):
        yield from self.__iter__()

    def __iter__(self):
        if self.left:
            for node in self.left.__iter__():
                yield node

        yield self

        if self.right:
            for node in self.right.__iter__():
                yield node

    def __reverse__(self):
        if self.right:
            for node in self.right.__reverse__():
                yield node
        yield self
        if self.left:
            for node in self.left.__reverse__():
                yield node

    def __init__(self, key, value):
        self.key = key
        self.val = value
        self.parent = self.left = self.right = None

    def __repr__(self):
        depth = self.depth()
        height = min(depth, 6)
        width = 16 * depth
        canvas = [[" " for i in range(width)] for j in range(height)]

        def write_on_canvas(x, y, chars):
            for i, character in enumerate(chars):
                if y + i == width:
                    return
                canvas[x][y + i] = character

        def paint(lo, hi, node, lvl):
            if lo > hi:
                return

            mid = lo + (hi - lo) // 2
            if lvl == 5:
                return write_on_canvas(lvl, mid - 1, "...")

            half = (mid - lo) // 2
            if node.left:
                write_on_canvas(lvl, lo + half, "┌" + "─" * half)
                paint(lo, mid - 1, node.left, lvl + 1)
            if node.right:
                write_on_canvas(lvl, mid + 1, "─" * half + "┐")
                paint(mid + 1, hi, node.right, lvl + 1)

            val = str(node)
            write_on_canvas(lvl, mid - len(val) // 2, val)

        paint(0, width - 2, self, 0)
        tree_preview = "\n".join("".join(row) for row in canvas)
        return f"Depth={depth}\n{tree_preview}"

    def __str__(self):
        return str(self.key)

    def num_nodes(self):
        return 1 + (self.left.num_nodes() if self.left else 0) + (self.right.num_nodes() if self.right else 0)


class bst:
    """Base class for binary search tree implementations."""

    root: bstnode

    def __init__(self):
        self.count = 0
        self.root = None

        # These two are currently used for slicing
        self.min_so_far = None
        self.max_so_far = None

    def insert(self, key, value=None):
        raise Exception("Not implemented")

    def remove(self, key):
        raise Exception("Not implemented")

    def iter(self, value=True, reverse=False):
        """
        A function that iterates through the nodes of the RedBlackTree in a specified order.

        Parameters:
            value (bool): A boolean indicating whether to yield the values of the nodes or the nodes themselves.
            reverse (bool): A boolean indicating whether to iterate in reverse order.

        Yields:
            The values of the nodes if 'value' is True, else the nodes themselves.
        """
        if not self.root:
            return list()
        generator = self.root.__reverse__() if reverse else self.root.__iter__()
        for node in generator:
            yield node.val if value else node

    def find(self, key, node=False):
        if not self.root:
            return
        _node = self._find_node(self.root, key)
        if not _node:
            return _node
        return _node if node else getattr(_node, "val", None)

    def __contains__(self, key):
        node = self._find_node(self.root, key) if self.root else None
        return True if node else False

    def __getitem__(self, key):
        if type(key) is slice:
            left = key.start if key.start != None else self.min_so_far
            right = key.stop if key.stop != None else self.max_so_far

            return list(bstslice(self, left, right))

        else:
            node = self._find_node(self.root, key) if self.root else None
            return node.val if node else None

    def __setitem__(self, key, value):
        self.insert(key, value)

    def __delitem__(self, key):
        self.remove(key)

    def __iter__(self):
        return self.inorder()

    def __eq__(self, other):
        def equal(node1, node2):
            if (not node1 and node2) or (not node2 and node1):
                return False
            if node1.key != node2.key or node1.val != node2.val:
                return False

            if node1.left or node2.left:
                if not equal(node1.left, node2.left):
                    return False
            if node1.right or node2.right:
                if not equal(node1.right, node2.right):
                    return False
            return True

        if self.root == other.root:
            return True
        return equal(self.root, other.root)

    def __len__(self):
        return self.root.num_nodes() if self.root else 0

    def depth(self):
        """Returns the depth of the tree"""
        if not self.root:
            return 0

        return self.root.depth()

    def inorder(self):
        return self.root.inorder() if self.root else empty_generator()

    def _find_node(self, node, key):
        if node.key == key:
            return node
        elif key < node.key:
            return self._find_node(node.left, key) if node.left else None
        return self._find_node(node.right, key) if node.right else None

    def _find_node_margin(self, node, key):
        if node.key == key:
            return node

        if key < node.key:
            if node.left:
                return self._find_node_margin(node.left, key)
            return node

        if node.right:
            return self._find_node_margin(node.right, key)
        return node

    def _find_max(self, node):
        if node.right:
            return self._find_max(node.right)
        return node

    def _find_min(self, node):
        if node.left:
            return self._find_min(node.left)
        return node

    def _insert_node(self, start, to_insert):
        """
        Inserts a given node (not value) into the tree without any rebalancing.
        Returns True if was inserted False if it was updated
        """

        def insert_internal(current_node):
            if to_insert.key < current_node.key:
                if current_node.left:
                    return insert_internal(current_node.left)

                current_node.left = to_insert
                to_insert.parent = current_node
                self.count += 1
                return True

            elif to_insert.key > current_node.key:
                if current_node.right:
                    return insert_internal(current_node.right)

                current_node.right = to_insert
                to_insert.parent = current_node
                self.count += 1
                return True

            current_node.val = to_insert.val
            return False

        self.min_so_far = min(self.min_so_far, to_insert.key) if self.min_so_far != None else to_insert.key
        self.max_so_far = max(self.max_so_far, to_insert.key) if self.max_so_far != None else to_insert.key

        if not self.root:
            self.root = to_insert
            self.count += 1
        else:
            return insert_internal(start)

    def _rotate_right(self, y):
        """
          T0   T0                         T0   T0
            \ /                             \ /
             y                               x
            / \     right Rotation          /  \
           x   T3   - - - - - - - >        T1   y
          / \       < - - - - - - -            / \
         T1  T2     left Rotation            T2  T3
        """
        x = y.left

        # Attach T2 to y
        T2 = x.right
        if T2:
            T2.parent = y
        y.left = T2

        # Attach x to T0
        if y == self.root:
            self.root = x
            x.parent = None
        else:
            T0 = y.parent
            if T0.left == y:
                T0.left = x
            else:
                T0.right = x
            x.parent = T0

        # Attach y to x
        y.parent = x
        x.right = y

    def _rotate_left(self, x):
        """
          T0   T0                         T0   T0
            \ /                             \ /
             y                               x
            / \     right Rotation          /  \
           x   T3   - - - - - - - >        T1   y
          / \       < - - - - - - -            / \
         T1  T2     left Rotation            T2  T3
        """

        y = x.right

        # Attach T2 to x
        T2 = y.left
        if T2:
            T2.parent = x
        x.right = T2

        if x == self.root:
            self.root = y
            y.parent = None
        else:
            # Attach T0 to y
            T0 = x.parent
            if T0.left == x:
                T0.left = y
            else:
                T0.right = y
            y.parent = T0

        # Attach x to y
        x.parent = y
        y.left = x

    def __repr__(self):
        if not self.root:
            return "Empty Tree"

        return repr(self.root)


class rbnode(bstnode):
    colored: bool

    def __init__(self, key, value, color):
        super().__init__(key, value)
        self.colored = color

    def __str__(self):
        str_val = ":" + str(self.val) if self.val != None else ""
        return f'{self.key}{str_val if len(str_val) < 10 else str_val[:8] + ".."}'
        # return str(self.key) + ('(b)' if self.colored else '(r)')


class rbtree(bst):
    left = 0
    right = 1

    def __init__(self, initializer=None):
        super().__init__()
        self.rotations = [[None, None], [None, None]]
        self.rotations[rbtree.left][rbtree.left] = self._rebalance_ll
        self.rotations[rbtree.left][rbtree.right] = self._rebalance_lr
        self.rotations[rbtree.right][rbtree.left] = self._rebalance_rl
        self.rotations[rbtree.right][rbtree.right] = self._rebalance_rr

        self.fixups = [[None, None, None, None], [None, None, None, None]]
        self.fixups[rbtree.left][0] = self._fixup_left_1
        self.fixups[rbtree.left][1] = self._fixup_left_2
        self.fixups[rbtree.left][2] = self._fixup_left_3
        self.fixups[rbtree.left][3] = self._fixup_4

        self.fixups[rbtree.right][0] = self._fixup_right_1
        self.fixups[rbtree.right][1] = self._fixup_right_2
        self.fixups[rbtree.right][2] = self._fixup_right_3
        self.fixups[rbtree.right][3] = self._fixup_4

        if initializer:
            if type(initializer) == dict:
                for k, v in initializer.items():
                    self.insert(k, v)
            else:
                for k in initializer:
                    if type(k) is tuple:
                        self.insert(key=k[0], value=k[1])
                    else:
                        self.insert(key=k)

    def _check_valid(self):
        def enum_black_heights(node, prev_colored=True, black_height=0):
            if not node.colored and not prev_colored:
                raise Exception("Invalid RBTree: Red parent has Red children")

            if node.colored:
                black_height += 1

            if node.left:
                if node.left.key > node.key:
                    raise Exception("Invalid RBTree: Not a valid BST")

                for bh in enum_black_heights(node.left, node.colored, black_height):
                    yield bh
            if node.right:
                if node.right.key < node.key:
                    raise Exception("Invalid RBTree: Not a valid BST")

                for bh in enum_black_heights(node.right, node.colored, black_height):
                    yield bh

            if not node.left and not node.right:
                yield black_height

        if not self.root:
            return True

        black_heights = enum_black_heights(self.root)
        black_height = next(black_heights)
        for bh in black_heights:
            if bh != black_height:
                raise Exception("Invalid RBTree: black heights not equal")

    def _rebalance_ll(self, gparent, parent):
        self._rotate_right(gparent)
        gparent.colored = not gparent.colored
        parent.colored = not parent.colored

        return parent

    def _rebalance_lr(self, gparent, parent):
        node = parent.right
        self._rotate_left(parent)
        return self._rebalance_ll(gparent, node)

    def _rebalance_rl(self, gparent, parent):
        node = parent.left
        self._rotate_right(parent)
        return self._rebalance_rr(gparent, node)

    def _rebalance_rr(self, gparent, parent):
        self._rotate_left(gparent)
        gparent.colored = not gparent.colored
        parent.colored = not parent.colored

        return parent

    def _fixup_left_1(self, node, parent, sibling):
        """
        Sibling is red
            b               r                 b
          /   \           /   \             /   \
        node   r    =>   b      y     =>   r      y
             /   \      /  \              /  \
            x     y   node  x           node  x
        Solution: rotate parent left. swap colors between parent and sibling and continue
        """
        sibling.colored = True
        parent.colored = False
        self._rotate_left(parent)
        self._remove_fixup(node)

    def _fixup_right_1(self, node, parent, sibling):
        """Mirror left case 1"""
        sibling.colored = True
        parent.colored = False
        self._rotate_right(parent)
        self._remove_fixup(node)

    def _fixup_left_2(self, node, parent, sibling):
        """
            ?               b              ?
          /   \           /   \          /   \
        node   b    =>   ?     r  =>    b     b
             /   \      /  \           /  \
            x     r   node  x        node  x
        Solution: switch colors between parent and sibling then rotate parent left and color nephew black
        """
        sibling.colored = parent.colored
        parent.colored = True
        sibling.right.colored = True
        self._rotate_left(parent)

    def _fixup_right_2(self, node, parent, sibling):
        """Mirror of left case 2"""
        sibling.colored = parent.colored
        parent.colored = True
        sibling.left.colored = True
        self._rotate_right(parent)

    def _fixup_left_3(self, node, parent, sibling):
        """
            ?                  ?
          /   \              /   \
        node   b    =>     node   b    =>
             /   \                  \
            r     b                  r
                                      \
                                       b

        Solution: convert to case 2 by rotating sibling to right and swapping color between niece and sibling
        """
        sibling.colored = False
        sibling.left.colored = True
        self._rotate_right(sibling)
        self._remove_fixup(node)

    def _fixup_right_3(self, node, parent, sibling):
        """Mirror of left case 3"""
        sibling.colored = False
        sibling.right.colored = True
        self._rotate_left(sibling)
        self._remove_fixup(node)

    def _fixup_4(self, node, parent, sibling):
        """
            ?              ?
          /   \          /   \
        node   b    => node   r
             /   \          /   \
            b     b        b     b
        Color sibling red and continue from parent
        """
        sibling.colored = False
        self._remove_fixup(parent)

    def _rebalance(self, node):
        parent = node.parent
        if not parent or node.colored or parent.colored:
            return

        grandparent = parent.parent
        if not grandparent:
            return

        dir_parent = rbtree.left if grandparent.left == parent else rbtree.right
        uncle = grandparent.right if dir_parent == rbtree.left else grandparent.left

        if uncle and not uncle.colored:
            uncle.colored = parent.colored = True
            grandparent.colored = grandparent == self.root
            self._rebalance(grandparent)
        else:
            dir_node = rbtree.left if parent.left == node else rbtree.right
            self._rebalance(self.rotations[dir_parent][dir_node](grandparent, parent))

    def _remove_fixup(self, node):
        if node == self.root:
            return
        if not node.colored:
            node.colored = True
            return

        parent = node.parent
        if parent.left == node:
            dir = rbtree.left
            sibling = parent.right
            niece, nephew = sibling.left, sibling.right
        else:
            dir = rbtree.right
            sibling = parent.left
            niece, nephew = sibling.right, sibling.left

        if not sibling.colored:
            self.fixups[dir][0](node, parent, sibling)
        elif nephew and not nephew.colored:
            self.fixups[dir][1](node, parent, sibling)
        elif niece and not niece.colored:
            self.fixups[dir][2](node, parent, sibling)
        else:
            self.fixups[dir][3](node, parent, sibling)

    def insert(self, key, value=None):
        node = rbnode(key, value, False if self.root else True)
        if self._insert_node(self.root, node):
            self._rebalance(node)

    def remove(self, key):
        if not self.root:
            return

        leaf = node = self._find_node(self.root, key)
        if node == None:
            return

        # Swap node to delete key & value at leaf
        while leaf:
            if node.left:
                leaf = self._find_max(node.left)
            elif node.right:
                leaf = self._find_min(node.right)
            else:
                break

            node.key, leaf.key = leaf.key, node.key
            node.val, leaf.val = leaf.val, node.val
            node = leaf

        # Fixup rbtree
        self._remove_fixup(leaf)

        # Remove leaf
        if leaf == self.root:
            self.root = None
        else:
            parent = leaf.parent
            if parent.left == leaf:
                leaf.parent.left = None
            else:
                leaf.parent.right = None
            leaf.parent = None
        self.count -= 1


def rbtree_from_array(arr):
    tree = rbtree()
    size_arr = len(arr)
    if size_arr == 0:
        return tree

    stack = [(0, None, False)]
    while stack:
        idx, parent, is_left = stack.pop()
        key, val = arr[idx] if type(arr[idx]) is tuple else (arr[idx], None)
        if not key:
            continue

        node = rbnode(key=key, value=val, color=True)

        if parent:
            if is_left:
                if node.key >= parent.key:
                    raise Exception(f"Invalid BST {node.key} >= {parent.key}")
                parent.left = node
            else:
                if node.key <= parent.key:
                    raise Exception(f"Invalid BST {node.key} <= {parent.key}")
                parent.right = node
            node.parent = parent
        else:
            tree.root = node

        idx_left = idx * 2 + 1
        idx_right = idx * 2 + 2
        if idx_left < size_arr:
            stack.append((idx_left, node, True))
        if idx_right < size_arr:
            stack.append((idx_right, node, False))

    return tree


def test_ll_rr_insertions():
    tree = rbtree()
    tree.insert(1)
    assert tree == rbtree_from_array([1]), "Failed to insert into empty tree"

    tree = rbtree()
    tree.insert(3)
    tree.insert(2)
    tree.insert(1)
    assert tree == rbtree_from_array([2, 1, 3]), "Failed insertion/rebalance in simple L->L->L branch"

    tree.insert(4)
    assert tree == rbtree_from_array([2, 1, 3, None, None, None, 4]), "Failed insertion/rebalance in L->L->L branch"

    tree.insert(5)
    assert tree == rbtree_from_array([2, 1, 4, None, None, 3, 5]), "Failed insertion/rebalance in R->R->R branch"


def test_still_valid_tree_after_insertion():
    tree = rbtree()
    for num in [randint(0, 100) for i in range(100)]:
        tree.insert(num)
        try:
            tree._check_valid()
        except Exception as e:
            raise AssertionError(e)


def test_correctly_inserted_keys():
    tree = rbtree()
    nums = [randint(0, 100) for i in range(100)]

    for num in nums:
        tree.insert(num, num**2)

    for num in nums:
        assert num in tree, "Inserted key is not in tree"
        assert tree[num] == num**2, f"Inserted key value is not correct Key:{num}, Expected:{num**2} Actual:{tree[num]}"

    nums = set([i for i in range(100)]) - set(nums)
    for num in nums:
        assert num not in tree, "Not inserted key is in tree"
        assert tree[num] == None, "Not inserted key value is not None"


def test_rbtree_slicing():
    assert rbtree()[:] == [], "Slicing empty tree does not work"

    nums = [(i, i + 1) for i in range(100)]
    shuffle(nums)
    sorted_nums = sorted(nums)

    tree = rbtree(nums)
    assert tree[:] == sorted_nums, "Slicing whole tree does not yield all elements"

    for i in range(20):
        a, b = randint(0, 100), randint(0, 100)
        assert sorted_nums[a : b + 1] == tree[a:b], f"Random slice doesnt yield correct elements tree[{a}:{b}]"


def test_rbtree_insert_override():
    tree = rbtree({i: None for i in range(10)})
    tree.insert(5, "Something")
    assert tree[5] == "Something", "Inserting the same key does not override the value"


def test_rbtree_constructor():
    assert rbtree([1, 2, 3, 4, 5])[:] == [
        (1, None),
        (2, None),
        (3, None),
        (4, None),
        (5, None),
    ], f"Simple list constructor doesnt work"

    nums = [(i, i + 1) for i in range(5)]
    assert rbtree(nums)[:] == nums, "List with (key, val) tuples constructor doesnt work"

    nums2 = {i: i + 1 for i in range(5)}
    assert rbtree(nums2)[:] == nums, "Dict constructor doesnt work"


def test_rbtree_equals():
    t1, t2 = rbtree({i: i + 1 for i in range(5)}), rbtree({i: i + 1 for i in range(5)})
    assert t1 == t2, "List equality doesnt work (1)"

    t1.insert(100, 1)
    assert t1 != t2, "List equality doesnt work (2)"


def test_traversals():

    nums = {i: i + 1 for i in range(50)}
    for node in rbtree(nums):
        assert node.val == nums[node.key], "Invalid inorder traversal"


def test_still_valid_rbtree_after_remove():

    nums = [randint(0, 2000) for i in range(1000)]
    tree = rbtree(nums)
    shuffle(nums)

    for num in nums:
        tree.remove(num)
        try:
            tree._check_valid()
        except Exception as e:
            raise AssertionError(e)


def test_keys_correctly_removed():

    nums = [i for i in range(50)]
    tree = rbtree([(i, i + 1) for i in range(50)])

    for i in range(len(nums)):
        num = nums[i]

        assert num in tree, "Inserted key not in tree"
        tree.remove(num)
        assert num not in tree, "Removed key still in tree"

        for num2 in nums[i + 1 :]:
            assert num2 in tree, f"Key removal removed more than 1 key (removed: {num}, missing: {num2})"
            assert tree[num2] == num2 + 1, "Key removal messed up values of other nodes"


def test_remove_edge_cases():
    t1, t2 = rbtree([1, 2, 3, 4, 5]), rbtree([1, 2, 3, 4, 5])
    t1.remove(6)
    assert t1 == t2, "Removing inexisting key has side effects"

    t1, t2 = rbtree([1]), rbtree()
    t1.remove(1)
    assert t1 == t2, "Fails to remove the root"


def test_len():
    tree = rbtree()
    assert len(tree) == 0, "Empty tree length is not 0"

    for i in range(10):
        tree.insert(i)
        assert len(tree) == i + 1, "Invalid tree length after insertion"

    for i in range(10, -1, -1):
        tree.remove(i)
        assert len(tree) == i, "Invalid tree length after removal"


def run_rbtree_tests():
    tests = {
        ("Test left-left, right-right insertion", test_ll_rr_insertions),
        ("Test Keys inserted correctly         ", test_correctly_inserted_keys),
        ("Test Valid RBTree after inserts      ", test_still_valid_tree_after_insertion),
        ("Test Slicing                         ", test_rbtree_slicing),
        ("Test Insert Override                 ", test_rbtree_insert_override),
        ("Test __init__                        ", test_rbtree_constructor),
        ("Test __eq__                          ", test_rbtree_equals),
        ("Test Traversals                      ", test_traversals),
        ("Test Valid RBTree after removes      ", test_still_valid_rbtree_after_remove),
        ("Test Keys removed correctly          ", test_keys_correctly_removed),
        ("Test Remove edge cases               ", test_remove_edge_cases),
        ("Test Tree __len__                    ", test_len),
    }

    for test_name, test in tests:
        try:
            print(f"Running [{test_name}]", end="")
            test()
            print(" Succeeded")
        except AssertionError as e:
            print(f" Failed => {e}")


if __name__ == "__main__":
    run_rbtree_tests()

    # red_black_tree = RedBlackTree()
    red_black_tree = rbtree()

    red_black_tree.insert(-1, "-1")
    red_black_tree.insert(0, "0")
    red_black_tree.insert(1, "1")
    red_black_tree.insert(2, "2")
    red_black_tree.insert(3, "3")
    red_black_tree.insert(9, "9")
    red_black_tree.insert(10, "10")
    red_black_tree.insert(10, "10")
    red_black_tree.insert(4, "4")
    red_black_tree.insert(5, "5")
    red_black_tree.insert(6, "6")
    red_black_tree.insert(7, "7")
    red_black_tree.insert(8, "8")
    # red_black_tree.insert('a', "a")
    r1 = red_black_tree.find(7)
    r2 = red_black_tree.find(10)
    print(r1)
    print(r2)
    n = red_black_tree.count
    print(n)
    for node in red_black_tree:
        print(node.key, node.val)

    for node in red_black_tree.iter(value=False, reverse=True):
        print(node.key, node.val)
