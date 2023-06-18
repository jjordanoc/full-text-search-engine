from functools import total_ordering
from typing import TypeVar, Generic, List, Optional
import heapq

T = TypeVar('T')


@total_ordering
class MaxHeapWrapper(Generic[T]):
    def __init__(self, val: T) -> None:
        self.val = val

    def __lt__(self, other) -> bool:
        return self.val > other.val

    def __eq__(self, other) -> bool:
        return self.val == other.val


class MaxHeap(Generic[T]):

    def __init__(self, val: Optional[List[T]] = None) -> None:
        if val is not None:
            self.heap: List[MaxHeapWrapper[T]] = list(map(lambda item: MaxHeapWrapper[T](item), val))
            heapq.heapify(self.heap)
        else:
            self.heap = []

    def push(self, val: T) -> None:
        heapq.heappush(self.heap, MaxHeapWrapper[T](val))

    def pop(self) -> T:
        return heapq.heappop(self.heap).val

    def empty(self):
        return len(self.heap) == 0


class MinHeap(Generic[T]):

    def __init__(self, val: Optional[List[T]] = None) -> None:
        if val is not None:
            self.heap: List[T] = list(map(lambda item: item, val))
            heapq.heapify(self.heap)
        else:
            self.heap = []

    def push(self, val: T) -> None:
        heapq.heappush(self.heap, val)

    def pop(self) -> T:
        return heapq.heappop(self.heap)

    def empty(self):
        return len(self.heap) == 0


if __name__ == "__main__":
    heap = MinHeap([10, 20, 400, 30])
    while not heap.empty():
        print(heap.pop())
