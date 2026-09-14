! rule: C708
! covers: class-dummy class-allocatable class-pointer
! evidence: positive-control
program c708_class_eligibility
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload), target :: seed = payload(3)
    class(payload), pointer :: alias => null()
    class(payload), allocatable :: copy
    alias => seed
    if (.not. associated(alias)) error stop 'association'
    allocate(payload :: copy)
    if (.not. allocated(copy)) error stop 'allocation'
    copy%code = 7
    call inspect(alias)
    if (copy%code /= 7) error stop 'copy'
contains
    subroutine inspect(value)
        class(payload), intent(in) :: value
        if (value%code /= 3) error stop 'dummy'
    end subroutine
end program
