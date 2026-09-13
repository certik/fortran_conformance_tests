! rule: C1401
! Explicit boundaries keep these main programs in separate compilations.
! case: mismatched-name
program c1401_start
    implicit none
end program c1401_other ! {error C1401 mismatched-name}
! case: named-without-program
    implicit none
    integer :: n
    n = 1
end program c1401_missing ! {error C1401 named-without-program}
! case: distinct-final-character
program c1401_name_a
    implicit none
end program c1401_name_b ! {error C1401 distinct-final-character}
