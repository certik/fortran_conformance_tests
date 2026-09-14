! rule: R603
! covers: initial-letter alphanumeric-suffix
! evidence: positive-control
! Free-form repairs: prefix a letter to 1name and _name; replace @ in @name.
! Replace the special character in bad$name and bad@name with an underscore.
program names_repairs
    implicit none
    integer :: a1name, a_name, aname, bad_name

    a1name = 43
    a_name = 47
    aname = 53
    bad_name = 59

    if (a1name /= 43) error stop 1
    if (a_name /= 47) error stop 2
    if (aname /= 53) error stop 3
    if (bad_name /= 59) error stop 4
end program names_repairs
