! rule: C709
! covers: typeof-component classof-component
! evidence: positive-control
! standard: f2023
program c709_components
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload) :: seed = payload(3)
    type :: container
        typeof(seed) :: plain
        classof(seed), allocatable :: poly
    end type
    type(container) :: object
    object%plain%code = 7
    allocate(payload :: object%poly)
    if (.not. allocated(object%poly)) error stop 'allocation'
    object%poly%code = 11
    if (object%plain%code /= 7 .or. object%poly%code /= 11) error stop 'values'
end program
