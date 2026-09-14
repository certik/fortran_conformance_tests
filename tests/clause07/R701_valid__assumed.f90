! rule: R701
! covers: assumed-token
! evidence: positive-control
program type_parameters_assumed_token
    implicit none
    call check_text('ABC')
contains
    subroutine check_text(text)
        character(len=*), intent(in) :: text
        if (len(text) /= 3) error stop 1
        if (text /= 'ABC') error stop 2
    end subroutine check_text
end program type_parameters_assumed_token
