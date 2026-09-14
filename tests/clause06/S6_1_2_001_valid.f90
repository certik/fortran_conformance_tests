! rule: S6.1.2-001
! covers: uppercase-letter-repertoire lowercase-letter-repertoire
! evidence: effect
program letterrepertoire
    implicit none
    character(len=52) :: letters
    integer :: i, j

    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    do i = 1, len(letters)
        do j = i + 1, len(letters)
            if (letters(i:i) == letters(j:j)) error stop 1
        end do
    end do
end program letterrepertoire
