! rule: C708
! covers: classof-dummy classof-allocatable classof-pointer
! evidence: positive-control
! standard: f2023
program c708_classof_eligibility
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload), target :: seed = payload(3)
    classof(seed), pointer :: alias => null()
    classof(seed), allocatable :: copy
    alias => seed
    if (.not. associated(alias)) error stop 'association'
    allocate(payload :: copy)
    if (.not. allocated(copy)) error stop 'allocation'
    copy%code = 7
    call inspect(alias)
    if (copy%code /= 7) error stop 'copy'
contains
    subroutine inspect(value)
        classof(seed), intent(in) :: value
        if (value%code /= 3) error stop 'dummy'
    end subroutine
end program
