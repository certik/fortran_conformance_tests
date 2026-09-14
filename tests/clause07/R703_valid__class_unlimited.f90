! rule: R703
! covers: class-unlimited
! evidence: positive-control
program r703_class_unlimited
    implicit none
    class(*), allocatable :: value
    allocate(integer :: value)
    if (.not. allocated(value)) error stop 'allocation'
    select type (value)
    type is (integer)
        value = 7
        if (value /= 7) error stop 'value'
    class default
        error stop 'type'
    end select
end program
