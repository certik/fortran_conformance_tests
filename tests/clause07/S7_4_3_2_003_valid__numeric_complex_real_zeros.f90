! rule: S7.4.3.2-003
! covers: mixed-kind-and-type-relations
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    real :: rp = +0.0, rn = -0.0
    double precision :: dp = +0.0d0, dn = -0.0d0
    complex :: c = (0.0, 0.0)
    complex(kind(0.0d0)) :: dc = (0.0d0, 0.0d0)
    if (.not. (rp == c)) error stop 1
    if (rp /= c) error stop 2
    if (.not. (rp .eq. c)) error stop 3
    if (rp .ne. c) error stop 4
    if (.not. (rp == dc)) error stop 5
    if (rp /= dc) error stop 6
    if (.not. (rp .eq. dc)) error stop 7
    if (rp .ne. dc) error stop 8
    if (.not. (rn == c)) error stop 9
    if (rn /= c) error stop 10
    if (.not. (rn .eq. c)) error stop 11
    if (rn .ne. c) error stop 12
    if (.not. (rn == dc)) error stop 13
    if (rn /= dc) error stop 14
    if (.not. (rn .eq. dc)) error stop 15
    if (rn .ne. dc) error stop 16
    if (.not. (dp == c)) error stop 17
    if (dp /= c) error stop 18
    if (.not. (dp .eq. c)) error stop 19
    if (dp .ne. c) error stop 20
    if (.not. (dp == dc)) error stop 21
    if (dp /= dc) error stop 22
    if (.not. (dp .eq. dc)) error stop 23
    if (dp .ne. dc) error stop 24
    if (.not. (dn == c)) error stop 25
    if (dn /= c) error stop 26
    if (.not. (dn .eq. c)) error stop 27
    if (dn .ne. c) error stop 28
    if (.not. (dn == dc)) error stop 29
    if (dn /= dc) error stop 30
    if (.not. (dn .eq. dc)) error stop 31
    if (dn .ne. dc) error stop 32
    if (.not. (c == rp)) error stop 33
    if (c /= rp) error stop 34
    if (.not. (c .eq. rp)) error stop 35
    if (c .ne. rp) error stop 36
    if (.not. (dc == rp)) error stop 37
    if (dc /= rp) error stop 38
    if (.not. (dc .eq. rp)) error stop 39
    if (dc .ne. rp) error stop 40
    if (.not. (c == rn)) error stop 41
    if (c /= rn) error stop 42
    if (.not. (c .eq. rn)) error stop 43
    if (c .ne. rn) error stop 44
    if (.not. (dc == rn)) error stop 45
    if (dc /= rn) error stop 46
    if (.not. (dc .eq. rn)) error stop 47
    if (dc .ne. rn) error stop 48
    if (.not. (c == dp)) error stop 49
    if (c /= dp) error stop 50
    if (.not. (c .eq. dp)) error stop 51
    if (c .ne. dp) error stop 52
    if (.not. (dc == dp)) error stop 53
    if (dc /= dp) error stop 54
    if (.not. (dc .eq. dp)) error stop 55
    if (dc .ne. dp) error stop 56
    if (.not. (c == dn)) error stop 57
    if (c /= dn) error stop 58
    if (.not. (c .eq. dn)) error stop 59
    if (c .ne. dn) error stop 60
    if (.not. (dc == dn)) error stop 61
    if (dc /= dn) error stop 62
    if (.not. (dc .eq. dn)) error stop 63
    if (dc .ne. dn) error stop 64
end program numeric_literal_case
