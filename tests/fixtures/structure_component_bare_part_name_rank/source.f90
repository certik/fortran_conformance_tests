! rule: S9.4.2-002
! covers: bare-part-name-rank
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_bare_part_name_rank
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
  checks=0
  x(2)%alpha = 239
  x(3)%alpha = 313
  x(2)%beta = 299
  if (x(2)%alpha /= 239) then
    write(*,'(a)') 'SC:bare_part_name_rank:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 299) then
    write(*,'(a)') 'SC:bare_part_name_rank:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:bare_part_name_rank:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%avec = [911, 919, 929]
  obj%bvec = [941, 947, 953]
  if (any(shape(obj%avec) /= [3])) then
    write(*,'(a)') 'SC:bare_part_name_rank:shape'
    error stop
  end if
  checks=checks+1
  if (any(lbound(obj%avec) /= [-5])) then
    write(*,'(a)') 'SC:bare_part_name_rank:lbound'
    error stop
  end if
  checks=checks+1
  if (any(ubound(obj%avec) /= [-3])) then
    write(*,'(a)') 'SC:bare_part_name_rank:ubound'
    error stop
  end if
  checks=checks+1
  if (any(obj%avec /= [911, 919, 929])) then
    write(*,'(a)') 'SC:bare_part_name_rank:values'
    error stop
  end if
  checks=checks+1
  if (any(obj%bvec /= [941, 947, 953])) then
    write(*,'(a)') 'SC:bare_part_name_rank:neighbor-vector-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 8) then
    write(*,'(a)') 'SC:bare_part_name_rank:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT BARE PART NAME RANK OK'
end program structure_component_bare_part_name_rank
