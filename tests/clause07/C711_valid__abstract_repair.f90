! rule: C711
! covers: concrete-declared-type
! evidence: positive-control
! standard: f2023
program c711_abstract
    implicit none
    type :: root
        integer :: code
    end type
    class(root), allocatable :: seed
    typeof(seed), allocatable :: copy
end program
