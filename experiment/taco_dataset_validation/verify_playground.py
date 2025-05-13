import math

# Solution 1: Iterative approach keeping track of product's first digits
def firstdigit_solution1(arr, n):
    p = 1
    for i in range(n):
        p = p * arr[i]
        d = str(p)
        p = int(d[:6])  # Keep only first few digits to avoid overflow
    return int(str(p)[0])

# Solution 2: Logarithm-based approach to extract first digit
def firstdigit_solution2(arr, n):
    s = 0.0
    for a in arr:
        s += math.log10(a)
    s = s - math.floor(s)
    return int(math.pow(10, s) + 1e-06)

# Solution 3: Iterative product calculation and extracting first digit
def firstdigit_solution3(arr, n):
    product = 1
    for i in range(0, n):
        product = product * arr[i]
    digit = product // 10 ** int(math.log10(product))
    return digit

# Example test cases
test_cases = [
    (4, [5, 8, 3, 7]),  # Expected output: 8
    (3, [6, 7, 9])       # Expected output: 3
]

# Running all solutions on test cases
results_solution1 = [firstdigit_solution1(arr, n) for n, arr in test_cases]
results_solution2 = [firstdigit_solution2(arr, n) for n, arr in test_cases]
results_solution3 = [firstdigit_solution3(arr, n) for n, arr in test_cases]

print(results_solution1, results_solution2, results_solution3)


def faro_cycles(deck_size):
    # For a deck with only 2 cards, one shuffle returns it to original order.
    if deck_size == 2:
        return 1
    # The number of faro shuffles needed is the smallest k such that 2^k mod (deck_size - 1) equals 1.
    k = 1
    while pow(2, k, deck_size - 1) != 1:
        k += 1
    return k

# Testing the function with the provided example inputs.
if __name__ == '__main__':
    test_cases = [2, 6, 52, 542, 1250, 1954]
    for tc in test_cases:
        result = faro_cycles(tc)
        print(f'faro_cycles({tc}) = {result}')

# Expected output:
# faro_cycles(2) = 1
# faro_cycles(52) = 8
# faro_cycles(542) = 540
# faro_cycles(1250) = 156
# faro_cycles(1954) = 30


#Example that doesn't work