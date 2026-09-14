! rule: R603
! covers: alphanumeric-suffix
! Free-form source; each special character is in the Fortran character set,
! but neither is a letter, digit, or underscore permitted inside a name.
! case: suffix-dollar
program bad_suffix_dollar
    implicit none
    integer :: bad$name ! {error R603 suffix-dollar}
end program bad_suffix_dollar
! case: suffix-at
program bad_suffix_at
    implicit none
    integer :: bad@name ! {error R603 suffix-at}
end program bad_suffix_at
