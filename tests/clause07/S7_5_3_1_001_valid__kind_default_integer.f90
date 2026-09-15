! rule: S7.5.3.1-001
! covers: default-kind-parameter-integer-kind
! evidence: effect
! standard: f2023
program parameter_probe
    implicit none

    type :: packet(tag)
        integer, kind :: tag
        integer :: payload
    end type
    type(packet(2)) :: item
    item%payload = 7
    if (item%tag /= 2) error stop 1
    if (kind(item%tag) /= kind(0)) error stop 2
    call check(item%tag)
contains
    subroutine check(value)
        integer(kind(0)), intent(in) :: value
        if (value /= 2) error stop 3
    end subroutine
end program
