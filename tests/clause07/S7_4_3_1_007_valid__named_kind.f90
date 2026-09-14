! rule: S7.4.3.1-007
! covers: named-kind-decimal
! evidence: effect
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: value
    data value /000123456789012345678_k/
    if (value /= 123456789_k * 1000000000_k + 12345678_k) error stop 1
end program
