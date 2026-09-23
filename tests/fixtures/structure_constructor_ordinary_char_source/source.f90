! rule: S7.5.10-009
! covers: ordinary-character-deferred-length
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_ordinary_char_source_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    character(:), allocatable :: text
  end type record
  character(len=3) :: source
  checks=0
  source='LMN'
  call observe(record(101, 103, text=source))
  if (checks /= 6) then
    write(*,'(a)') 'DTSC:ordinary_char_source:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR ORDINARY CHAR SOURCE OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:ordinary_char_source:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:ordinary_char_source:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:ordinary_char_source:default-stamp'
      error stop
    end if
    checks=checks+1
    if (.not. (allocated(obj%text))) then
      write(*,'(a)') 'DTSC:ordinary_char_source:text-allocated'
      error stop
    end if
    checks=checks+1
    if (len(obj%text) /= 3) then
      write(*,'(a)') 'DTSC:ordinary_char_source:text-len'
      error stop
    end if
    checks=checks+1
    if (obj%text /= 'LMN') then
      write(*,'(a)') 'DTSC:ordinary_char_source:text-value'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_ordinary_char_source_effect
