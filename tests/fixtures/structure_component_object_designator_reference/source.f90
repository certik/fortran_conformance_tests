! rule: S9.4.2-001
! covers: object-designator-reference
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_object_designator_reference
  implicit none
  type :: cell_t
    integer :: alpha
    integer :: beta
    integer :: avec(-5:-3)
    integer :: bvec(-5:-3)
    integer :: grid(-4:-2,5:8)
    integer :: other_grid(-4:-2,5:8)
  end type cell_t
  type(cell_t) :: obj, x(2:6)
  integer :: checks
  integer :: observed
  checks=0
  x(2)%alpha = 223
  x(3)%alpha = 313
  x(2)%beta = 291
  if (x(2)%alpha /= 223) then
    write(*,'(a)') 'SC:object_designator_reference:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 291) then
    write(*,'(a)') 'SC:object_designator_reference:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:object_designator_reference:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%alpha = 337
  obj%beta = 449
  observed = obj%alpha + 19
  if (observed /= 356) then
    write(*,'(a)') 'SC:object_designator_reference:expression-reference'
    error stop
  end if
  checks=checks+1
  obj%alpha = obj%alpha + 23
  if (obj%alpha /= 360) then
    write(*,'(a)') 'SC:object_designator_reference:defined-component-reference'
    error stop
  end if
  checks=checks+1
  if (obj%beta /= 449) then
    write(*,'(a)') 'SC:object_designator_reference:neighbor-unchanged'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'SC:object_designator_reference:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT OBJECT DESIGNATOR REFERENCE OK'
end program structure_component_object_designator_reference
