! rule: S7.3.2.3-001
! covers: previous-derived function-prefix-host
! evidence: positive-control
program class_previous_host
    implicit none
    type :: packet
        integer :: tag
    end type
    class(packet), allocatable :: value
    integer :: status = -1
    allocate(value, source=make(), stat=status)
    if (status /= 0) error stop 'caller-allocation'
    if (.not. allocated(value)) error stop 'caller-unallocated'
    if (value%tag /= 43) error stop 'host-prefix-result'
    deallocate(value)
contains
    class(packet) function make() result(r)
        allocatable :: r
        integer :: ios
        ios = -1
        allocate(packet :: r, stat=ios)
        if (ios /= 0) error stop 'result-allocation'
        if (.not. allocated(r)) error stop 'result-unallocated'
        r%tag = 43
    end function
end program
