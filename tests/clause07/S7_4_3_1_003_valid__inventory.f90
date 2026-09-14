! rule: S7.4.3.1-003
! covers: range-eighteen
! evidence: effect
! profile: integer-literal-bounded-inventory
! standard: f2023
program p
    use iso_fortran_env, only: integer_kinds
    implicit none
    integer, parameter :: n = size(integer_kinds)
    integer, parameter :: k1 = integer_kinds(min(1, n))
    integer, parameter :: k2 = integer_kinds(min(2, n))
    integer, parameter :: k3 = integer_kinds(min(3, n))
    integer, parameter :: k4 = integer_kinds(min(4, n))
    integer, parameter :: k5 = integer_kinds(min(5, n))
    integer, parameter :: k6 = integer_kinds(min(6, n))
    integer, parameter :: k7 = integer_kinds(min(7, n))
    integer, parameter :: k8 = integer_kinds(min(8, n))
    integer, parameter :: k9 = integer_kinds(min(9, n))
    integer, parameter :: k10 = integer_kinds(min(10, n))
    integer, parameter :: k11 = integer_kinds(min(11, n))
    integer, parameter :: k12 = integer_kinds(min(12, n))
    integer, parameter :: k13 = integer_kinds(min(13, n))
    integer, parameter :: k14 = integer_kinds(min(14, n))
    integer, parameter :: k15 = integer_kinds(min(15, n))
    integer, parameter :: k16 = integer_kinds(min(16, n))
    integer :: ranges(16)
    if (n < 1 .or. n > 16) error stop 1
    ranges(1) = range(0_k1)
    ranges(2) = range(0_k2)
    ranges(3) = range(0_k3)
    ranges(4) = range(0_k4)
    ranges(5) = range(0_k5)
    ranges(6) = range(0_k6)
    ranges(7) = range(0_k7)
    ranges(8) = range(0_k8)
    ranges(9) = range(0_k9)
    ranges(10) = range(0_k10)
    ranges(11) = range(0_k11)
    ranges(12) = range(0_k12)
    ranges(13) = range(0_k13)
    ranges(14) = range(0_k14)
    ranges(15) = range(0_k15)
    ranges(16) = range(0_k16)
    if (maxval(ranges) < 18) error stop 2
    print *, 'advertised_kind_count', n
    print *, 'advertised_ranges', ranges(1:n)
end program
