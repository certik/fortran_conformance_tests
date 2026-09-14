! rule: C712
! covers: unlimited-data-ref
! evidence: positive-control
! standard: f2023
program c712_assumed_type
    implicit none
contains
    subroutine inspect(seed)
        class(*), intent(in) :: seed
        classof(seed), allocatable :: copy
    end subroutine
end program
