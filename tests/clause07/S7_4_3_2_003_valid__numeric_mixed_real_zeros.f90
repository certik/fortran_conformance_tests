! rule: S7.4.3.2-003
! covers: mixed-kind-and-type-relations
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    real :: rp = +0.0, rn = -0.0
    double precision :: dp = +0.0d0, dn = -0.0d0
    if (.not. (rp == dp)) error stop 1
    if (rp /= dp) error stop 2
    if (rp < dp) error stop 3
    if (.not. (rp <= dp)) error stop 4
    if (rp > dp) error stop 5
    if (.not. (rp >= dp)) error stop 6
    if (.not. (rp .eq. dp)) error stop 7
    if (rp .ne. dp) error stop 8
    if (rp .lt. dp) error stop 9
    if (.not. (rp .le. dp)) error stop 10
    if (rp .gt. dp) error stop 11
    if (.not. (rp .ge. dp)) error stop 12
    if (.not. (rp == dn)) error stop 13
    if (rp /= dn) error stop 14
    if (rp < dn) error stop 15
    if (.not. (rp <= dn)) error stop 16
    if (rp > dn) error stop 17
    if (.not. (rp >= dn)) error stop 18
    if (.not. (rp .eq. dn)) error stop 19
    if (rp .ne. dn) error stop 20
    if (rp .lt. dn) error stop 21
    if (.not. (rp .le. dn)) error stop 22
    if (rp .gt. dn) error stop 23
    if (.not. (rp .ge. dn)) error stop 24
    if (.not. (rn == dp)) error stop 25
    if (rn /= dp) error stop 26
    if (rn < dp) error stop 27
    if (.not. (rn <= dp)) error stop 28
    if (rn > dp) error stop 29
    if (.not. (rn >= dp)) error stop 30
    if (.not. (rn .eq. dp)) error stop 31
    if (rn .ne. dp) error stop 32
    if (rn .lt. dp) error stop 33
    if (.not. (rn .le. dp)) error stop 34
    if (rn .gt. dp) error stop 35
    if (.not. (rn .ge. dp)) error stop 36
    if (.not. (rn == dn)) error stop 37
    if (rn /= dn) error stop 38
    if (rn < dn) error stop 39
    if (.not. (rn <= dn)) error stop 40
    if (rn > dn) error stop 41
    if (.not. (rn >= dn)) error stop 42
    if (.not. (rn .eq. dn)) error stop 43
    if (rn .ne. dn) error stop 44
    if (rn .lt. dn) error stop 45
    if (.not. (rn .le. dn)) error stop 46
    if (rn .gt. dn) error stop 47
    if (.not. (rn .ge. dn)) error stop 48
    if (.not. (dp == rp)) error stop 49
    if (dp /= rp) error stop 50
    if (dp < rp) error stop 51
    if (.not. (dp <= rp)) error stop 52
    if (dp > rp) error stop 53
    if (.not. (dp >= rp)) error stop 54
    if (.not. (dp .eq. rp)) error stop 55
    if (dp .ne. rp) error stop 56
    if (dp .lt. rp) error stop 57
    if (.not. (dp .le. rp)) error stop 58
    if (dp .gt. rp) error stop 59
    if (.not. (dp .ge. rp)) error stop 60
    if (.not. (dn == rp)) error stop 61
    if (dn /= rp) error stop 62
    if (dn < rp) error stop 63
    if (.not. (dn <= rp)) error stop 64
    if (dn > rp) error stop 65
    if (.not. (dn >= rp)) error stop 66
    if (.not. (dn .eq. rp)) error stop 67
    if (dn .ne. rp) error stop 68
    if (dn .lt. rp) error stop 69
    if (.not. (dn .le. rp)) error stop 70
    if (dn .gt. rp) error stop 71
    if (.not. (dn .ge. rp)) error stop 72
    if (.not. (dp == rn)) error stop 73
    if (dp /= rn) error stop 74
    if (dp < rn) error stop 75
    if (.not. (dp <= rn)) error stop 76
    if (dp > rn) error stop 77
    if (.not. (dp >= rn)) error stop 78
    if (.not. (dp .eq. rn)) error stop 79
    if (dp .ne. rn) error stop 80
    if (dp .lt. rn) error stop 81
    if (.not. (dp .le. rn)) error stop 82
    if (dp .gt. rn) error stop 83
    if (.not. (dp .ge. rn)) error stop 84
    if (.not. (dn == rn)) error stop 85
    if (dn /= rn) error stop 86
    if (dn < rn) error stop 87
    if (.not. (dn <= rn)) error stop 88
    if (dn > rn) error stop 89
    if (.not. (dn >= rn)) error stop 90
    if (.not. (dn .eq. rn)) error stop 91
    if (dn .ne. rn) error stop 92
    if (dn .lt. rn) error stop 93
    if (.not. (dn .le. rn)) error stop 94
    if (dn .gt. rn) error stop 95
    if (.not. (dn .ge. rn)) error stop 96
end program numeric_literal_case
