module enum_value_observer
implicit none
private
public :: check_definition
contains
subroutine check_definition(tag,actual,expected,kind_agrees)
integer, intent(in) :: tag,actual(:),expected(:)
logical, intent(in) :: kind_agrees
if (size(actual)/=size(expected)) then
print *, 'ENUM_SIZE_MISMATCH',tag
error stop 101
end if
if (size(actual)==0) then
print *, 'ENUM_EMPTY_OBSERVATION',tag
error stop 102
end if
if (any(actual/=expected)) then
print *, 'ENUM_VALUE_MISMATCH',tag
print *, actual
error stop 104
end if
if (.not.kind_agrees) then
print *, 'ENUM_KIND_MISMATCH',tag
error stop 105
end if
end subroutine check_definition
end module enum_value_observer
program enum_values
use enum_value_observer, only: check_definition
implicit none
enum, bind(c)
enumerator :: flat_zero,flat_one,flat_four=4,flat_five,flat_nine=9,flat_ten,flat_reset=4,flat_next
end enum
enum, bind(c)
enumerator :: split_zero,split_one,split_four=4
enumerator :: split_five,split_nine=9,split_ten,split_reset=4,split_next
end enum
enum, bind(c)
enumerator :: negative_start=-3,negative_next
enumerator :: negative_four=4,negative_repeat=4,negative_five
end enum
enum, bind(c)
enumerator :: fresh_zero,fresh_one
end enum
! definition: flat
call check_definition(2, &
    [int(flat_zero),int(flat_one),int(flat_four),int(flat_five), &
     int(flat_nine),int(flat_ten),int(flat_reset),int(flat_next)], &
    [0,1,4,5,9,10,4,5], &
    all([kind(flat_zero),kind(flat_one),kind(flat_four),kind(flat_five), &
     kind(flat_nine),kind(flat_ten),kind(flat_reset),kind(flat_next)] == kind(flat_zero)))
! definition: split
call check_definition(3, &
    [int(split_zero),int(split_one),int(split_four),int(split_five), &
     int(split_nine),int(split_ten),int(split_reset),int(split_next)], &
    [0,1,4,5,9,10,4,5], &
    all([kind(split_zero),kind(split_one),kind(split_four),kind(split_five), &
     kind(split_nine),kind(split_ten),kind(split_reset),kind(split_next)] == kind(split_zero)))
! definition: negative
call check_definition(4, &
    [int(negative_start),int(negative_next),int(negative_four),int(negative_repeat), &
     int(negative_five)], &
    [-3,-2,4,4,5], &
    all([kind(negative_start),kind(negative_next),kind(negative_four),kind(negative_repeat), &
     kind(negative_five)] == kind(negative_start)))
! definition: fresh
call check_definition(5, &
    [int(fresh_zero),int(fresh_one)], &
    [0,1], &
    all([kind(fresh_zero),kind(fresh_one)] == kind(fresh_zero)))
end program enum_values
