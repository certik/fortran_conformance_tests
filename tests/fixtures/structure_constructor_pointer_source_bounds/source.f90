! rule: S7.5.10-007
! covers: pointer-source-association-and-bounds
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_pointer_source_bounds_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer, pointer :: p(:)
  end type record
  integer, target :: target(3)
  integer, pointer :: source(:)
  checks=0
  target(1)=11
  target(2)=13
  target(3)=17
  source(5:7) => target
  call observe(record(101, 103, p=source), source)
  if (checks /= 9) then
    write(*,'(a)') 'DTSC:pointer_source_bounds:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR POINTER SOURCE BOUNDS OK'
contains
  subroutine observe(obj, source)
    type(record), intent(in) :: obj
    integer, pointer, intent(in) :: source(:)
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:pointer_source_bounds:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:pointer_source_bounds:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:pointer_source_bounds:default-stamp'
      error stop
    end if
    checks=checks+1
    if (.not. (associated(obj%p, source))) then
      write(*,'(a)') 'DTSC:pointer_source_bounds:associated-with-source-pointer'
      error stop
    end if
    checks=checks+1
    if (lbound(obj%p,1) /= 5) then
      write(*,'(a)') 'DTSC:pointer_source_bounds:pointer-lbound'
      error stop
    end if
    checks=checks+1
    if (ubound(obj%p,1) /= 7) then
      write(*,'(a)') 'DTSC:pointer_source_bounds:pointer-ubound'
      error stop
    end if
    checks=checks+1
    if (obj%p(5) /= 11) then
      write(*,'(a)') 'DTSC:pointer_source_bounds:pointer-value-5'
      error stop
    end if
    checks=checks+1
    if (obj%p(6) /= 13) then
      write(*,'(a)') 'DTSC:pointer_source_bounds:pointer-value-6'
      error stop
    end if
    checks=checks+1
    if (obj%p(7) /= 17) then
      write(*,'(a)') 'DTSC:pointer_source_bounds:pointer-value-7'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_pointer_source_bounds_effect
