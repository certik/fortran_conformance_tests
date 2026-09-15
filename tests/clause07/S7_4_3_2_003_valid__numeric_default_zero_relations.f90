! rule: S7.4.3.2-003
! covers: zero-exists all-relational-spellings
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    real :: u, p, n
    data u, p, n /0.0, +0.0, -0.0/
    if (u /= 0.0) error stop 100
    if (.not. (p == p)) error stop 1
    if (p /= p) error stop 2
    if (p < p) error stop 3
    if (.not. (p <= p)) error stop 4
    if (p > p) error stop 5
    if (.not. (p >= p)) error stop 6
    if (.not. (p .eq. p)) error stop 7
    if (p .ne. p) error stop 8
    if (p .lt. p) error stop 9
    if (.not. (p .le. p)) error stop 10
    if (p .gt. p) error stop 11
    if (.not. (p .ge. p)) error stop 12
    if (.not. (p == n)) error stop 13
    if (p /= n) error stop 14
    if (p < n) error stop 15
    if (.not. (p <= n)) error stop 16
    if (p > n) error stop 17
    if (.not. (p >= n)) error stop 18
    if (.not. (p .eq. n)) error stop 19
    if (p .ne. n) error stop 20
    if (p .lt. n) error stop 21
    if (.not. (p .le. n)) error stop 22
    if (p .gt. n) error stop 23
    if (.not. (p .ge. n)) error stop 24
    if (.not. (n == p)) error stop 25
    if (n /= p) error stop 26
    if (n < p) error stop 27
    if (.not. (n <= p)) error stop 28
    if (n > p) error stop 29
    if (.not. (n >= p)) error stop 30
    if (.not. (n .eq. p)) error stop 31
    if (n .ne. p) error stop 32
    if (n .lt. p) error stop 33
    if (.not. (n .le. p)) error stop 34
    if (n .gt. p) error stop 35
    if (.not. (n .ge. p)) error stop 36
    if (.not. (n == n)) error stop 37
    if (n /= n) error stop 38
    if (n < n) error stop 39
    if (.not. (n <= n)) error stop 40
    if (n > n) error stop 41
    if (.not. (n >= n)) error stop 42
    if (.not. (n .eq. n)) error stop 43
    if (n .ne. n) error stop 44
    if (n .lt. n) error stop 45
    if (.not. (n .le. n)) error stop 46
    if (n .gt. n) error stop 47
    if (.not. (n .ge. n)) error stop 48
end program numeric_literal_case
