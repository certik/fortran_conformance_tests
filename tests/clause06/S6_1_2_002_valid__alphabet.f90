! rule: S6.1.2-002
! covers: all-letter-name-equivalence
! evidence: effect
program alphabetcase
    implicit none
    integer :: A, B, C, D, E, F, G, H, I, J, K, L, M
    integer :: N, O, P, Q, R, S, T, U, V, W, X, Y, Z

    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i = 9
    j = 10
    k = 11
    l = 12
    m = 13
    n = 14
    o = 15
    p = 16
    q = 17
    r = 18
    s = 19
    t = 20
    u = 21
    v = 22
    w = 23
    x = 24
    y = 25
    z = 26
    if (A /= 1) error stop 1
    if (B /= 2) error stop 2
    if (C /= 3) error stop 3
    if (D /= 4) error stop 4
    if (E /= 5) error stop 5
    if (F /= 6) error stop 6
    if (G /= 7) error stop 7
    if (H /= 8) error stop 8
    if (I /= 9) error stop 9
    if (J /= 10) error stop 10
    if (K /= 11) error stop 11
    if (L /= 12) error stop 12
    if (M /= 13) error stop 13
    if (N /= 14) error stop 14
    if (O /= 15) error stop 15
    if (P /= 16) error stop 16
    if (Q /= 17) error stop 17
    if (R /= 18) error stop 18
    if (S /= 19) error stop 19
    if (T /= 20) error stop 20
    if (U /= 21) error stop 21
    if (V /= 22) error stop 22
    if (W /= 23) error stop 23
    if (X /= 24) error stop 24
    if (Y /= 25) error stop 25
    if (Z /= 26) error stop 26
end program alphabetcase
