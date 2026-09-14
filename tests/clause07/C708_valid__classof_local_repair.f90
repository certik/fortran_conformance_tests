! rule: C708
! covers: classof-allocatable
! evidence: positive-control
! standard: f2023
program c708_classof_local
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload) :: seed = payload(3)
    classof(seed), allocatable :: value
end program
