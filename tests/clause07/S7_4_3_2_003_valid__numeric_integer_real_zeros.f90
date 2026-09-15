! rule: S7.4.3.2-003
! covers: mixed-kind-and-type-relations
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    real :: rp = +0.0, rn = -0.0
    double precision :: dp = +0.0d0, dn = -0.0d0
    integer :: i = 0
    if (.not. (rp == i)) error stop 1
    if (rp /= i) error stop 2
    if (rp < i) error stop 3
    if (.not. (rp <= i)) error stop 4
    if (rp > i) error stop 5
    if (.not. (rp >= i)) error stop 6
    if (.not. (rp .eq. i)) error stop 7
    if (rp .ne. i) error stop 8
    if (rp .lt. i) error stop 9
    if (.not. (rp .le. i)) error stop 10
    if (rp .gt. i) error stop 11
    if (.not. (rp .ge. i)) error stop 12
    if (.not. (rn == i)) error stop 13
    if (rn /= i) error stop 14
    if (rn < i) error stop 15
    if (.not. (rn <= i)) error stop 16
    if (rn > i) error stop 17
    if (.not. (rn >= i)) error stop 18
    if (.not. (rn .eq. i)) error stop 19
    if (rn .ne. i) error stop 20
    if (rn .lt. i) error stop 21
    if (.not. (rn .le. i)) error stop 22
    if (rn .gt. i) error stop 23
    if (.not. (rn .ge. i)) error stop 24
    if (.not. (dp == i)) error stop 25
    if (dp /= i) error stop 26
    if (dp < i) error stop 27
    if (.not. (dp <= i)) error stop 28
    if (dp > i) error stop 29
    if (.not. (dp >= i)) error stop 30
    if (.not. (dp .eq. i)) error stop 31
    if (dp .ne. i) error stop 32
    if (dp .lt. i) error stop 33
    if (.not. (dp .le. i)) error stop 34
    if (dp .gt. i) error stop 35
    if (.not. (dp .ge. i)) error stop 36
    if (.not. (dn == i)) error stop 37
    if (dn /= i) error stop 38
    if (dn < i) error stop 39
    if (.not. (dn <= i)) error stop 40
    if (dn > i) error stop 41
    if (.not. (dn >= i)) error stop 42
    if (.not. (dn .eq. i)) error stop 43
    if (dn .ne. i) error stop 44
    if (dn .lt. i) error stop 45
    if (.not. (dn .le. i)) error stop 46
    if (dn .gt. i) error stop 47
    if (.not. (dn .ge. i)) error stop 48
    if (.not. (i == rp)) error stop 49
    if (i /= rp) error stop 50
    if (i < rp) error stop 51
    if (.not. (i <= rp)) error stop 52
    if (i > rp) error stop 53
    if (.not. (i >= rp)) error stop 54
    if (.not. (i .eq. rp)) error stop 55
    if (i .ne. rp) error stop 56
    if (i .lt. rp) error stop 57
    if (.not. (i .le. rp)) error stop 58
    if (i .gt. rp) error stop 59
    if (.not. (i .ge. rp)) error stop 60
    if (.not. (i == rn)) error stop 61
    if (i /= rn) error stop 62
    if (i < rn) error stop 63
    if (.not. (i <= rn)) error stop 64
    if (i > rn) error stop 65
    if (.not. (i >= rn)) error stop 66
    if (.not. (i .eq. rn)) error stop 67
    if (i .ne. rn) error stop 68
    if (i .lt. rn) error stop 69
    if (.not. (i .le. rn)) error stop 70
    if (i .gt. rn) error stop 71
    if (.not. (i .ge. rn)) error stop 72
    if (.not. (i == dp)) error stop 73
    if (i /= dp) error stop 74
    if (i < dp) error stop 75
    if (.not. (i <= dp)) error stop 76
    if (i > dp) error stop 77
    if (.not. (i >= dp)) error stop 78
    if (.not. (i .eq. dp)) error stop 79
    if (i .ne. dp) error stop 80
    if (i .lt. dp) error stop 81
    if (.not. (i .le. dp)) error stop 82
    if (i .gt. dp) error stop 83
    if (.not. (i .ge. dp)) error stop 84
    if (.not. (i == dn)) error stop 85
    if (i /= dn) error stop 86
    if (i < dn) error stop 87
    if (.not. (i <= dn)) error stop 88
    if (i > dn) error stop 89
    if (.not. (i >= dn)) error stop 90
    if (.not. (i .eq. dn)) error stop 91
    if (i .ne. dn) error stop 92
    if (i .lt. dn) error stop 93
    if (.not. (i .le. dn)) error stop 94
    if (i .gt. dn) error stop 95
    if (.not. (i .ge. dn)) error stop 96
end program numeric_literal_case
