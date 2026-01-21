import math

def combinations(n, k):
    """Calculates nCk (n choose k). Returns 0 if k < 0 or k > n."""
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)

def calculate_pass_at_k(n: int, c: int, k: int) -> float:
    """
    Calculates pass@k metric: The probability that at least one of k generations is correct.
    Unbiased estimator: 1 - (combination(n-c, k) / combination(n, k))
    
    Args:
        n: Total number of samples.
        c: Number of correct samples.
        k: The k parameter (sample size to estimate for).
        
    Returns:
        float: Probability [0.0, 1.0]. Returns 0.0 if n < k.
    """
    if n < k:
        return 0.0
    
    if c == n:
        return 1.0

    # Probability that ALL k samples are incorrect
    # This is choosing k samples from the (n-c) incorrect ones
    prob_all_incorrect = combinations(n - c, k) / combinations(n, k)
    
    return 1.0 - prob_all_incorrect

def calculate_pass_all_k(n: int, c: int, k: int) -> float:
    """
    Calculates pass^k metric (custom definition): The probability that ALL k generations are correct.
    Estimator: combination(c, k) / combination(n, k)
    
    Args:
        n: Total number of samples.
        c: Number of correct samples.
        k: The k parameter.
        
    Returns:
        float: Probability [0.0, 1.0]. Returns 0.0 if n < k.
    """
    if n < k:
        return 0.0
    
    # Probability that ALL k samples are correct
    # This is choosing k samples from the c correct ones
    return combinations(c, k) / combinations(n, k)
