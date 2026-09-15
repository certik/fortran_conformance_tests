! rule: S7.4.4.3-004
! covers: boundary-and-repeated-pairs
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(*), parameter :: a = '''X'''
character(*), parameter :: a2 = ''''''
character(*), parameter :: q = """X"""
character(*), parameter :: q2 = """"""
if (len(a) /= 3 .or. len(q) /= 3) error stop 1
if (len(a2) /= 2 .or. len(q2) /= 2) error stop 2
if (a(2:2) /= 'X' .or. q(2:2) /= 'X') error stop 3
if (a(1:1) /= a2(1:1) .or. a(3:3) /= a2(2:2)) error stop 4
if (q(1:1) /= q2(1:1) .or. q(3:3) /= q2(2:2)) error stop 5
if (a(1:1) == q(1:1)) error stop 6
end program
