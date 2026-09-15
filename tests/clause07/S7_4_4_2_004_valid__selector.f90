! rule: S7.4.4.2-004
! covers: selector-inheritance
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(len=3) :: first, second, words(2)
first = 'ABC'
second = 'def'
words = ['GHI', 'jkl']
if (len(first) /= 3 .or. len(second) /= 3) error stop 1
if (len(words) /= 3 .or. len(words(2)) /= 3) error stop 2
if (first /= 'ABC' .or. second /= 'def') error stop 3
if (words(1) /= 'GHI' .or. words(2) /= 'jkl') error stop 4
end program
