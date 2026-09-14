! rule: C704
! covers: dummy-specification-length
! evidence: positive-control
program c704_length
    implicit none
    call inspect(3)
contains
    subroutine inspect(n)
        integer, intent(in) :: n
        character(len=n) :: text
        text = 'abc'
        if (len(text) /= 3) error stop 'length'
        if (text /= 'abc') error stop 'value'
    end subroutine
end program
