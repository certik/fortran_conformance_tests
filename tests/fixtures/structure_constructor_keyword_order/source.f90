! rule: S7.5.10-002
! covers: keyword-order-independent
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_keyword_order_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer :: left
    integer :: right
  end type record
  checks=0
  call observe(record(101, 103, right=13, left=11))
  if (checks /= 5) then
    write(*,'(a)') 'DTSC:keyword_order:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR KEYWORD ORDER OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:keyword_order:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:keyword_order:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:keyword_order:default-stamp'
      error stop
    end if
    checks=checks+1
    if (obj%left /= 11) then
      write(*,'(a)') 'DTSC:keyword_order:left-by-name'
      error stop
    end if
    checks=checks+1
    if (obj%right /= 13) then
      write(*,'(a)') 'DTSC:keyword_order:right-by-name'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_keyword_order_effect
