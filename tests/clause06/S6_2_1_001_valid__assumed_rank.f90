! rule: S6.2.1-001
! covers: double-dot
! evidence: positive-control
! standard: f2018
program token_assumed_rank_admission
    implicit none

    call check_rank(9)
contains
    subroutine check_rank(value)
        integer, intent(in) :: value(..)

        if (rank(value) /= 0) error stop 1
    end subroutine check_rank
end program token_assumed_rank_admission
