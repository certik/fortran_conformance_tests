! rule: S6.1.6-001
! covers: iso10646-internal-input-record
! evidence: positive-control
! profile: iso10646
! F2023 6.1.6 p1; 12.2.2 p1 and 12.4 p2.
program other_characters_internal_input
    implicit none
    integer, parameter :: ucs4 = selected_char_kind('ISO_10646')
    character(kind=ucs4, len=4) :: record
    character(kind=ucs4, len=1) :: first, last
    character(kind=ucs4, len=2) :: middle
    integer :: status

    ! No output operation is used to prepare the input oracle.
    record = char(9731, kind=ucs4) // ucs4_'bY' // char(937, kind=ucs4)
    first = ucs4_'?'
    middle = ucs4_'??'
    last = ucs4_'?'
    read(record, '(a1,a2,a1)', iostat=status) first, middle, last
    if (status /= 0) stop 1
    if (first /= char(9731, kind=ucs4)) stop 2
    if (middle /= ucs4_'bY') stop 3
    if (last /= char(937, kind=ucs4)) stop 4
    if (first == last) stop 5
end program
