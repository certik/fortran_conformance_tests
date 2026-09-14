! rule: S7.3.2.3-001
! covers: function-prefix-use
! evidence: positive-control
module class_prefix_use_types
    implicit none
    type :: packet
        integer :: tag
    end type
end module
program class_prefix_use
    use class_prefix_use_types, only: result_type => packet
    implicit none
    class(result_type), allocatable :: value
    integer :: status = -1
    allocate(value, source=make(), stat=status)
    if (status /= 0) error stop 'caller-allocation'
    if (.not. allocated(value)) error stop 'caller-unallocated'
    if (value%tag /= 47) error stop 'use-prefix-result'
    deallocate(value)
contains
    class(packet) function make() result(r)
        use class_prefix_use_types, only: packet
        implicit none
        allocatable :: r
        integer :: ios
        ios = -1
        allocate(packet :: r, stat=ios)
        if (ios /= 0) error stop 'result-allocation'
        if (.not. allocated(r)) error stop 'result-unallocated'
        r%tag = 47
    end function
end program
