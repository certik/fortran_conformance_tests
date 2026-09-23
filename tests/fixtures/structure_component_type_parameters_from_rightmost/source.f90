! rule: S9.4.2-003
! covers: type-parameters-from-rightmost
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_type_parameters_from_rightmost
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
  x(2)%alpha = 271
  x(3)%alpha = 313
  x(2)%beta = 337
  if (x(2)%alpha /= 271) then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 337) then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%text = 'KLMNO'
  obj%other_text = 'PQRST'
  obj%longer_text = 'ABCDEFG'
  if (len(obj%text) /= 5) then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:rightmost-character-length'
    error stop
  end if
  checks=checks+1
  if (obj%text /= 'KLMNO') then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:rightmost-character-value'
    error stop
  end if
  checks=checks+1
  if (len(obj%other_text) /= 5) then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:same-type-neighbor-length'
    error stop
  end if
  checks=checks+1
  if (obj%other_text /= 'PQRST') then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:same-type-neighbor-value'
    error stop
  end if
  checks=checks+1
  if (len(obj%longer_text) /= 7) then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:longer-component-length-control'
    error stop
  end if
  checks=checks+1
  if (obj%longer_text /= 'ABCDEFG') then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:longer-component-value-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 9) then
    write(*,'(a)') 'SC:type_parameters_from_rightmost:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT TYPE PARAMETERS FROM RIGHTMOST OK'
end program structure_component_type_parameters_from_rightmost
