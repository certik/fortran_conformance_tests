! rule: S9.4.2-003
! covers: type-from-rightmost
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_type_from_rightmost
  implicit none
  type :: cell_t
    integer :: alpha
    integer :: beta
    integer :: avec(-5:-3)
    integer :: bvec(-5:-3)
    integer :: grid(-4:-2,5:8)
    integer :: other_grid(-4:-2,5:8)
    character(len=5) :: text
    character(len=5) :: other_text
    character(len=7) :: longer_text
  end type cell_t
  type(cell_t) :: obj, x(2:6)
  integer :: checks
  checks=0
  x(2)%alpha = 269
  x(3)%alpha = 313
  x(2)%beta = 331
  if (x(2)%alpha /= 269) then
    write(*,'(a)') 'SC:type_from_rightmost:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 331) then
    write(*,'(a)') 'SC:type_from_rightmost:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:type_from_rightmost:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%alpha = 1231
  obj%beta = 1289
  obj%text = 'ABCDE'
  obj%other_text = 'UVWXY'
  if (obj%alpha + 37 /= 1268) then
    write(*,'(a)') 'SC:type_from_rightmost:integer-rightmost-expression'
    error stop
  end if
  checks=checks+1
  if (obj%alpha /= 1231) then
    write(*,'(a)') 'SC:type_from_rightmost:integer-rightmost-value'
    error stop
  end if
  checks=checks+1
  if (obj%beta /= 1289) then
    write(*,'(a)') 'SC:type_from_rightmost:integer-neighbor-beta-control'
    error stop
  end if
  checks=checks+1
  if (len(obj%text) /= 5) then
    write(*,'(a)') 'SC:type_from_rightmost:character-rightmost-length'
    error stop
  end if
  checks=checks+1
  if (obj%text /= 'ABCDE') then
    write(*,'(a)') 'SC:type_from_rightmost:character-rightmost-value'
    error stop
  end if
  checks=checks+1
  if (obj%other_text /= 'UVWXY') then
    write(*,'(a)') 'SC:type_from_rightmost:character-neighbor-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 9) then
    write(*,'(a)') 'SC:type_from_rightmost:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT TYPE FROM RIGHTMOST OK'
end program structure_component_type_from_rightmost
