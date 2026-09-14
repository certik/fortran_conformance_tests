! rule: C710
! covers: classof-implicit
! evidence: positive-control
! standard: f2023
program c710_classof_implicit
    implicit none
    type :: payload
        integer :: code
    end type
    call inspect()
contains
    subroutine inspect()
        implicit type(payload) (p)
        classof(prior), allocatable :: copy
        prior%code = 3
        allocate(payload :: copy)
        if (.not. allocated(copy)) error stop 'allocation'
        copy%code = 7
        if (prior%code /= 3 .or. copy%code /= 7) error stop 'values'
    end subroutine
end program
