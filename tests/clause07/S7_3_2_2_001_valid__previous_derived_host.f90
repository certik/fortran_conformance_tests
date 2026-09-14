! rule: S7.3.2.2-001
! covers: previous-derived function-prefix-host
! evidence: positive-control
program type_previous_derived_host
    implicit none
    type :: packet
        integer :: tag
    end type
    type(packet) :: value
    value%tag = -1
    value = make()
    if (value%tag /= 31) error stop 'host-result'
contains
    type(packet) function make() result(r)
        r%tag = 31
    end function
end program
