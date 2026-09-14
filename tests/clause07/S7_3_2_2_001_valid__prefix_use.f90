! rule: S7.3.2.2-001
! covers: function-prefix-use
! evidence: positive-control
module type_prefix_use_types
    implicit none
    type :: packet
        integer :: tag
    end type
end module
program type_prefix_use
    use type_prefix_use_types, only: result_type => packet
    implicit none
    type(result_type) :: value
    value%tag = -1
    value = make()
    if (value%tag /= 37) error stop 'use-result'
contains
    type(packet) function make() result(r)
        use type_prefix_use_types, only: packet
        implicit none
        r%tag = 37
    end function
end program
