! rule: S10.2.1.3-008
! covers: derived-length-parameters
! F2023 10.2.1.3 p3, bullet 2. Separate from character-only cases.
program s10_2_1_3_008_pdt
    implicit none
    type :: text_t(n)
        integer, len :: n
        character(n) :: text
    end type
    type(text_t(3)) :: short
    type(text_t(5)) :: long
    type(text_t(:)), allocatable :: copy
    short%text = 'abc'
    long%text = 'vwxyz'
    copy = short
    if (.not. allocated(copy)) error stop 'pdt-allocation'
    if (copy%n /= 3 .or. len(copy%text) /= 3) error stop 'pdt-initial-length'
    if (copy%text /= 'abc') error stop 'pdt-initial-value'
    copy = long
    if (copy%n /= 5 .or. len(copy%text) /= 5) error stop 'pdt-changed-length'
    if (copy%text /= 'vwxyz') error stop 'pdt-changed-value'
end program
