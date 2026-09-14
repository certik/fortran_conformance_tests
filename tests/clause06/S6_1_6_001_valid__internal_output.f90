! rule: S6.1.6-001
! covers: iso10646-internal-output-record
! evidence: positive-control
! profile: iso10646
! F2023 6.1.6 p1; 12.2.2 p1 and 12.4 p2.
program other_characters_internal_output
    implicit none
    integer, parameter :: ucs4 = selected_char_kind('ISO_10646')
    character(kind=ucs4, len=4) :: record
    integer :: status

    record = ucs4_'????'
    ! ISO-kind CHAR constructs the graphics without assuming source decoding.
    write(record, '(a1,a2,a1)', iostat=status) &
        char(937, kind=ucs4), ucs4_'Az', char(9731, kind=ucs4)
    if (status /= 0) stop 1
    if (record(1:1) /= char(937, kind=ucs4)) stop 2
    if (record(2:3) /= ucs4_'Az') stop 3
    if (record(4:4) /= char(9731, kind=ucs4)) stop 4
    if (record(1:1) == record(4:4)) stop 5
end program
