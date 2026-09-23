! rule: S9.4.2-003
! covers: rank-zero-when-no-nonzero-part-ref
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_rank_zero_when_no_nonzero_part_ref
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
  x(2)%alpha = 257
  x(3)%alpha = 313
  x(2)%beta = 311
  if (x(2)%alpha /= 257) then
    write(*,'(a)') 'SC:rank_zero_when_no_nonzero_part_ref:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 311) then
    write(*,'(a)') 'SC:rank_zero_when_no_nonzero_part_ref:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:rank_zero_when_no_nonzero_part_ref:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%alpha = 673
  obj%beta = 761
  obj%avec = [881, 883, 887]
  if (obj%alpha + 17 /= 690) then
    write(*,'(a)') 'SC:rank_zero_when_no_nonzero_part_ref:scalar-expression'
    error stop
  end if
  checks=checks+1
  if (obj%alpha /= 673) then
    write(*,'(a)') 'SC:rank_zero_when_no_nonzero_part_ref:scalar-component'
    error stop
  end if
  checks=checks+1
  if (obj%beta /= 761) then
    write(*,'(a)') 'SC:rank_zero_when_no_nonzero_part_ref:scalar-neighbor-beta-control'
    error stop
  end if
  checks=checks+1
  if (any(obj%avec /= [881, 883, 887])) then
    write(*,'(a)') 'SC:rank_zero_when_no_nonzero_part_ref:array-neighbor-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 7) then
    write(*,'(a)') 'SC:rank_zero_when_no_nonzero_part_ref:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT RANK ZERO WHEN NO NONZERO PART REF OK'
end program structure_component_rank_zero_when_no_nonzero_part_ref
