! rule: C712
! covers: derived-data-ref
! evidence: positive-control
! standard: f2023
program c712_intrinsic
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload) :: seed = payload(3)
    classof(seed), allocatable :: copy
end program
